import os, re, json, hmac, hashlib, sqlite3, argparse, threading
import urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone
from tkinter import Tk, StringVar, END, BOTH, LEFT, X, W, messagebox, simpledialog, filedialog
from tkinter import ttk

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "property_buyers.sqlite3"
EXA_URL = "https://api.exa.ai/search"
CITIES = ["Pune", "Lonavala", "Karjat", "Chakan", "Mumbai"]
PROPERTY_TYPES = ["Plot", "Flat", "Farmhouse"]

BUYER_TERMS = (
    "looking for", "looking to buy", "want to buy", "want to purchase",
    "need a plot", "need plot", "plot required", "flat required", "need a flat",
    "need flat", "farmhouse required", "need farmhouse", "buyer requirement",
    "purchase requirement", "seeking to buy", "in search of", "property chahiye",
    "plot chahiye", "flat chahiye", "ghar chahiye", "kharedi karaychi"
)
SELLER_TERMS = (
    "property for sale", "plots for sale", "flats for sale", "farmhouse for sale",
    "new launch", "project launch", "book your", "booking open", "contact our sales",
    "call our sales", "developer inventory", "builder offer", "rent available"
)
CONSENT_TERMS = (
    "i agree to be contacted", "i consent to be contacted", "you can call me",
    "please call me", "call me at", "contact me on whatsapp", "whatsapp me at",
    "you may contact me", "please contact me", "i authorize you to contact me",
    "mujhe call kar sakte ho", "mujhe whatsapp kar sakte ho", "aap mujhe contact kar sakte ho"
)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)


def now_text():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS public_discoveries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          city TEXT NOT NULL, property_type TEXT NOT NULL, title TEXT NOT NULL,
          url TEXT NOT NULL UNIQUE, published_date TEXT, evidence TEXT,
          intent_score INTEGER NOT NULL DEFAULT 0,
          review_status TEXT NOT NULL DEFAULT 'Needs manual review',
          discovered_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS inbound_leads (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          platform_user_id TEXT, username TEXT, event_type TEXT NOT NULL,
          message_text_redacted TEXT, city TEXT, property_type TEXT,
          budget_text TEXT, source_media_id TEXT, phone TEXT,
          contact_consent TEXT NOT NULL DEFAULT 'Not given',
          consent_evidence TEXT,
          review_status TEXT NOT NULL DEFAULT 'Needs manual review',
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS webhook_events (
          event_hash TEXT PRIMARY KEY, received_at TEXT NOT NULL,
          event_type TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_discoveries_city ON public_discoveries(city);
        CREATE INDEX IF NOT EXISTS idx_leads_city ON inbound_leads(city);
        """)
        con.commit()


def infer_type(text):
    t = (text or "").lower()
    if any(x in t for x in ("farmhouse", "farm house", "weekend home")): return "Farmhouse"
    if any(x in t for x in ("plot", "land", "residential land")): return "Plot"
    if any(x in t for x in ("flat", "apartment", "bhk")): return "Flat"
    return ""


def infer_city(text):
    t = (text or "").lower()
    return next((c for c in CITIES if c.lower() in t), "")


def infer_budget(text):
    patterns = [
      r"(?:₹|rs\.?\s*)\s?\d[\d,]*(?:\.\d+)?\s?(?:crore|cr|lakh|lac|lacs)?",
      r"\b\d+(?:\.\d+)?\s?(?:crore|crores|cr|lakh|lakhs|lac|lacs)\b"
    ]
    for pattern in patterns:
        m = re.search(pattern, text or "", re.I)
        if m: return m.group(0).strip()
    return ""


def buyer_score(text):
    t = (text or "").lower()
    positives = sum(term in t for term in BUYER_TERMS)
    negatives = sum(term in t for term in SELLER_TERMS)
    if not positives or negatives: return 0
    return min(100, positives * 25)


def exa_search(api_key, query, count):
    payload = {
      "query": query, "type": "auto", "numResults": int(count),
      "includeDomains": ["instagram.com"],
      "contents": {"highlights": {"numSentences": 3, "highlightsPerUrl": 2}}
    }
    req = urllib.request.Request(
      EXA_URL, data=json.dumps(payload).encode("utf-8"),
      headers={"x-api-key": api_key, "Content-Type": "application/json"},
      method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Exa HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc



def instagram_profile():
    """Verify the token and retrieve the connected Instagram professional account."""
    token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("INSTAGRAM_ACCESS_TOKEN is missing in your local .env file.")
    version = os.getenv("META_API_VERSION", "v27.0").strip()
    url = f"https://graph.instagram.com/{version}/me?fields=user_id,username"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            profile = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Instagram API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Instagram network error: {exc.reason}") from exc
    if not profile.get("username"):
        raise RuntimeError(f"Unexpected Instagram profile response: {profile}")
    return profile


def store_public_results(city, prop, results):
    saved = duplicates = filtered = 0
    with sqlite3.connect(DB_PATH) as con:
        for item in results:
            url = (item.get("url") or "").strip()
            if not url.startswith(("https://", "http://")) or "instagram.com" not in url.lower():
                filtered += 1
                continue
            title = (item.get("title") or "Instagram page").strip()
            highlights = item.get("highlights") or []
            evidence = "\n".join(str(x) for x in highlights) if isinstance(highlights, list) else str(highlights)
            full_text = title + "\n" + evidence
            score = buyer_score(full_text)
            found_type = infer_type(full_text)
            if score == 0 or (found_type and found_type != prop):
                filtered += 1
                continue
            try:
                con.execute("""
                  INSERT INTO public_discoveries
                  (city, property_type, title, url, published_date, evidence, intent_score, discovered_at)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (city, prop, title, url, item.get("publishedDate") or "",
                      evidence, score, now_text()))
                saved += 1
            except sqlite3.IntegrityError:
                duplicates += 1
        con.commit()
    return saved, duplicates, filtered


def explicit_consent(text):
    t = (text or "").lower()
    return any(term in t for term in CONSENT_TERMS)


def redact_contacts(text, keep_phone=False):
    value = text or ""
    if not keep_phone:
        value = PHONE_RE.sub("[phone withheld]", value)
    value = EMAIL_RE.sub("[email withheld]", value)
    return value


def save_inbound(text, sender_id, username, event_type, media_id, event_hash):
    text = text or ""
    prop = infer_type(text)
    score = buyer_score(text)
    # Require buyer intent; a bare mention of a flat or plot is not a lead.
    if score == 0:
        short_interest = ("interested in", "send details", "need details", "price details", "what is the price", "site visit", "looking", "need", "want to buy", "want to purchase", "required", "chahiye", "purchase")
        if not prop or not any(term in text.lower() for term in short_interest):
            return "not_a_property_lead"
        if any(term in text.lower() for term in SELLER_TERMS):
            return "not_a_property_lead"
    consent = explicit_consent(text)
    phone_match = PHONE_RE.search(text) if consent else None
    phone = phone_match.group(0) if phone_match else None
    safe_text = redact_contacts(text, keep_phone=bool(phone))
    consent_status = "Explicit opt-in" if consent else "In-app reply only"
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.execute(
          "INSERT OR IGNORE INTO webhook_events(event_hash, received_at, event_type) VALUES(?,?,?)",
          (event_hash, now_text(), event_type)
        )
        if cursor.rowcount == 0:
            return "duplicate"
        con.execute("""
          INSERT INTO inbound_leads
          (platform_user_id, username, event_type, message_text_redacted, city,
           property_type, budget_text, source_media_id, phone, contact_consent,
           consent_evidence, review_status, created_at)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
          sender_id, username, event_type, safe_text, infer_city(text), prop,
          infer_budget(text), media_id, phone, consent_status,
          "Consent phrase detected in inbound text" if consent else "",
          "Needs manual review", now_text()
        ))
        con.commit()
    return "saved"


def verify_signature(raw_body, signature, app_secret):
    if not app_secret or not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def run_webhook():
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        raise SystemExit("Install dependencies first: pip install -r requirements.txt")
    app = Flask(__name__)
    verify_token = os.getenv("META_VERIFY_TOKEN", "")
    app_secret = os.getenv("META_APP_SECRET", "")

    @app.get("/webhook")
    def verify():
        mode = request.args.get("hub.mode", "")
        token = request.args.get("hub.verify_token", "")
        challenge = request.args.get("hub.challenge", "")
        if mode == "subscribe" and verify_token and hmac.compare_digest(token, verify_token):
            return challenge, 200
        return "Verification failed", 403

    @app.post("/webhook")
    def receive():
        raw = request.get_data()
        if not verify_signature(raw, request.headers.get("X-Hub-Signature-256", ""), app_secret):
            return "Invalid signature", 403
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            return "Invalid JSON", 400
        saved = 0
        for entry in payload.get("entry", []):
            for event in entry.get("messaging", []) or []:
                msg = event.get("message") or {}
                if msg.get("is_echo") or not msg.get("text"): continue
                sender = event.get("sender") or {}
                digest = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
                saved += save_inbound(msg["text"], str(sender.get("id", "")), "",
                                      "instagram_dm", "", digest) == "saved"
            for change in entry.get("changes", []) or []:
                if change.get("field") != "comments": continue
                value = change.get("value") or {}
                author = value.get("from") or {}
                media = value.get("media") or {}
                digest = hashlib.sha256(json.dumps(change, sort_keys=True).encode()).hexdigest()
                saved += save_inbound(value.get("text", ""), str(author.get("id", "")),
                                      author.get("username", ""), "comment_on_own_media",
                                      str(media.get("id", "")), digest) == "saved"
        return jsonify({"ok": True, "saved_interactions": saved}), 200

    print("Webhook: http://127.0.0.1:5000/webhook")
    print("Meta requires a public HTTPS callback for live webhook events.")
    app.run(host="0.0.0.0", port=int(os.getenv("WEBHOOK_PORT", "5000")), debug=False)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Real Estate | Instagram Buyer Lead Intelligence")
        self.root.geometry("1300x780")
        self.api_key = os.getenv("EXA_API_KEY", "").strip()
        self.city = StringVar(value="Pune")
        self.prop = StringVar(value="Plot")
        self.extra = StringVar(value="")
        self.count = StringVar(value="10")
        self.status = StringVar(value="Ready. Exa can search indexed public pages; Meta setup comes after you create a professional account.")
        self.build()
        self.refresh()

    def build(self):
        head = ttk.Frame(self.root, padding=12); head.pack(fill=X)
        ttk.Label(head, text="PROPERTY BUYER INTELLIGENCE", font=("Segoe UI", 17, "bold")).pack(side=LEFT)
        ttk.Button(head, text="Set Exa API Key", command=self.set_key).pack(side="right")
        ttk.Button(head, text="Check Instagram Account", command=self.check_instagram).pack(side="right", padx=6)
        tabs = ttk.Notebook(self.root); tabs.pack(fill=BOTH, expand=True, padx=10, pady=5)
        self.pub_tab = ttk.Frame(tabs, padding=10); self.lead_tab = ttk.Frame(tabs, padding=10)
        tabs.add(self.pub_tab, text="Public Instagram Discovery")
        tabs.add(self.lead_tab, text="Inbound Leads - Own Account")
        form = ttk.LabelFrame(self.pub_tab, text="Search publicly indexed Instagram pages", padding=10)
        form.pack(fill=X)
        ttk.Label(form, text="City").grid(row=0, column=0, padx=4, pady=5)
        ttk.Combobox(form, textvariable=self.city, values=CITIES, state="readonly", width=14).grid(row=0, column=1, padx=4)
        ttk.Label(form, text="Property").grid(row=0, column=2, padx=4)
        ttk.Combobox(form, textvariable=self.prop, values=PROPERTY_TYPES, state="readonly", width=14).grid(row=0, column=3, padx=4)
        ttk.Label(form, text="Max results").grid(row=0, column=4, padx=4)
        ttk.Combobox(form, textvariable=self.count, values=["5","10","20"], state="readonly", width=6).grid(row=0, column=5, padx=4)
        ttk.Label(form, text="Extra keywords").grid(row=1, column=0, padx=4, pady=5)
        ttk.Entry(form, textvariable=self.extra, width=75).grid(row=1, column=1, columnspan=4, padx=4, sticky="ew")
        ttk.Button(form, text="Search", command=self.search).grid(row=1, column=5, padx=4)
        self.public_tree = self.make_tree(self.pub_tab,
          ("id","city","prop","title","published","score","review"),
          ("ID","City","Property","Page title","Published","Intent","Review"),
          (45,80,90,440,140,75,190))
        row = ttk.Frame(self.pub_tab); row.pack(fill=X)
        ttk.Button(row, text="Open source", command=self.open_source).pack(side=LEFT, padx=3)
        ttk.Button(row, text="Mark reviewed", command=self.mark_reviewed).pack(side=LEFT, padx=3)
        self.lead_tree = self.make_tree(self.lead_tab,
          ("id","username","event","city","prop","budget","consent","review"),
          ("ID","IG handle","Event","City","Property","Budget","Permission","Review"),
          (45,150,170,80,100,100,180,180))
        row2 = ttk.Frame(self.lead_tab); row2.pack(fill=X)
        ttk.Button(row2, text="Refresh", command=self.refresh).pack(side=LEFT, padx=3)
        ttk.Button(row2, text="Export CSV", command=self.export_csv).pack(side=LEFT, padx=3)
        ttk.Label(self.root, textvariable=self.status, relief="sunken", anchor="w", padding=7).pack(fill=X, side="bottom")

    def make_tree(self, parent, cols, labels, widths):
        frame = ttk.Frame(parent); frame.pack(fill=BOTH, expand=True)
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c, label, width in zip(cols, labels, widths):
            tree.heading(c, text=label); tree.column(c, width=width, anchor="w")
        y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=y.set)
        tree.grid(row=0, column=0, sticky="nsew"); y.grid(row=0, column=1, sticky="ns")
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        return tree

    def set_key(self):
        key = simpledialog.askstring("Exa API key", "Paste Exa API key (hidden):", show="*", parent=self.root)
        if key and key.strip():
            self.api_key = key.strip()
            self.status.set("Key is held in memory only; it is not saved to GitHub or the database.")

    def check_instagram(self):
        load_env()
        if not os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip():
            messagebox.showinfo(
                "Instagram not connected",
                "Create a professional Instagram account and Meta Developer app, generate an Instagram Login token, then add it to your local .env as INSTAGRAM_ACCESS_TOKEN."
            )
            return
        self.status.set("Checking Instagram professional account connection...")
        threading.Thread(target=self._check_instagram_worker, daemon=True).start()

    def _check_instagram_worker(self):
        try:
            profile = instagram_profile()
            username = profile.get("username", "connected")
            user_id = profile.get("user_id") or profile.get("id") or ""
            self.root.after(0, lambda: self._instagram_connected(username, user_id))
        except Exception as exc:
            self.root.after(0, lambda error=str(exc): self._instagram_connection_error(error))

    def _instagram_connected(self, username, user_id):
        self.status.set("Instagram connected: @" + username + " | account ID: " + str(user_id))
        messagebox.showinfo("Instagram connected", "Connected professional account: @" + username + "\nAccount ID: " + str(user_id))

    def _instagram_connection_error(self, error):
        self.status.set("Instagram connection check failed.")
        messagebox.showerror("Instagram API error", error)

    def search(self):
        if not self.api_key: self.set_key()
        if not self.api_key: return
        city, prop = self.city.get(), self.prop.get()
        query = (
          f"Instagram public post or Reel where an individual says they are looking to buy "
          f"or need a {prop} in {city}, Maharashtra. Buyer wording: looking for, need, "
          f"required, want to buy, want to purchase. Exclude sellers, property ads, "
          f"for-sale posts, broker advertisements and builders. {self.extra.get()}"
        )
        self.status.set(f"Searching public Instagram pages for buyer requirements in {city}...")
        threading.Thread(target=self.worker, args=(query, int(self.count.get()), city, prop), daemon=True).start()

    def worker(self, query, count, city, prop):
        try:
            data = exa_search(self.api_key, query, count)
            results = data.get("results", [])
            saved, dup, filtered = store_public_results(city, prop, results)
            cost_obj = data.get("costDollars", {})
            cost = cost_obj.get("total") if isinstance(cost_obj, dict) else None
            self.root.after(0, lambda: self.done(len(results), saved, dup, filtered, cost))
        except Exception as exc:
            self.root.after(0, lambda message=str(exc): messagebox.showerror("Exa error", message))

    def done(self, found, saved, dup, filtered, cost):
        self.refresh()
        self.status.set("Returned: " + str(found) + " | Saved buyer-intent candidates: " + str(saved) +
                        " | Duplicates: " + str(dup) + " | Filtered: " + str(filtered) +
                        (" | API cost: " + str(cost) if cost is not None else ""))
        messagebox.showinfo("Search finished",
          f"Pages returned: {found}\nBuyer-intent candidates saved: {saved}\nDuplicates: {dup}\nFiltered: {filtered}\n\n"
          "These are candidate pages, not confirmed buyers. Manually open and verify each result.")

    def refresh(self):
        if not hasattr(self, "public_tree"): return
        for t in (self.public_tree, self.lead_tree):
            for row in t.get_children(): t.delete(row)
        with sqlite3.connect(DB_PATH) as con:
            for r in con.execute("SELECT id,city,property_type,title,published_date,intent_score,review_status FROM public_discoveries ORDER BY id DESC"):
                self.public_tree.insert("", END, values=r)
            for r in con.execute("SELECT id,COALESCE(username,''),event_type,COALESCE(city,''),COALESCE(property_type,''),COALESCE(budget_text,''),contact_consent,review_status FROM inbound_leads ORDER BY id DESC"):
                self.lead_tree.insert("", END, values=r)

    def selected_public_id(self):
        selected = self.public_tree.selection()
        if not selected:
            messagebox.showwarning("Select row", "Select a discovery result first."); return None
        return self.public_tree.item(selected[0], "values")[0]

    def open_source(self):
        import webbrowser
        row_id = self.selected_public_id()
        if not row_id: return
        with sqlite3.connect(DB_PATH) as con:
            row = con.execute("SELECT url FROM public_discoveries WHERE id=?", (row_id,)).fetchone()
        if row: webbrowser.open(row[0])

    def mark_reviewed(self):
        row_id = self.selected_public_id()
        if not row_id: return
        with sqlite3.connect(DB_PATH) as con:
            con.execute("UPDATE public_discoveries SET review_status='Reviewed - buyer not yet confirmed' WHERE id=?", (row_id,))
            con.commit()
        self.refresh()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="instagram_inbound_leads.csv",
                                            filetypes=[("CSV files","*.csv")], parent=self.root)
        if not path: return
        with sqlite3.connect(DB_PATH) as con:
            rows = con.execute("SELECT * FROM inbound_leads ORDER BY id DESC").fetchall()
            headers = [r[1] for r in con.execute("PRAGMA table_info(inbound_leads)")]
        import csv
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f); writer.writerow(headers); writer.writerows(rows)
        messagebox.showinfo("Export complete", "Exported " + str(len(rows)) + " inbound interactions.")


def main():
    load_env(); init_db()
    parser = argparse.ArgumentParser()
    parser.add_argument("--webhook", action="store_true", help="Run Meta webhook receiver")
    parser.add_argument("--check-instagram", action="store_true", help="Verify Instagram Login token and connected professional account")
    args = parser.parse_args()
    if args.webhook:
        run_webhook()
    elif args.check_instagram:
        print(json.dumps(instagram_profile(), indent=2))
    else:
        root = Tk(); App(root); root.mainloop()


if __name__ == "__main__":
    main()
