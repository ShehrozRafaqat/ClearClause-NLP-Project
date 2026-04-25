"""
ClearClause – Configuration & Clause Definitions
All 14 legal clause types with risk mappings, keyword patterns, and metadata.
"""

# ─── App Meta ─────────────────────────────────────────────────────────────────
APP_NAME    = "ClearClause"
APP_VERSION = "1.0.0"
APP_TAGLINE = "AI-Powered Contract Risk Analyzer for Freelancers & Professionals"
GROQ_MODEL  = "llama3-8b-8192"

# ─── Risk Thresholds ──────────────────────────────────────────────────────────
RISK_THRESHOLDS = {"safe": 33, "moderate": 66}  # scores above 66 → HIGH RISK

# ─── Clause Definitions ───────────────────────────────────────────────────────
# Each entry: risk_level, risk_score (contribution), keywords, simplify hint,
#             why_it_matters, icon, color
CLAUSE_DEFINITIONS = {
    "IP Ownership / Work-for-Hire": {
        "risk_level": "HIGH",
        "risk_score": 30,
        "icon": "🔴",
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "keywords": [
            "intellectual property", "work for hire", "work-for-hire",
            "ip ownership", "assigns all right", "all rights title",
            "perpetual license", "irrevocable license", "all intellectual",
            "owns all work", "right title and interest",
        ],
        "simplify_hint": "who owns intellectual property and creative work",
        "why_it_matters": (
            "This clause determines who owns the work you produce. "
            "If ownership is assigned to the client, you lose all rights "
            "to the code, design, or content you created — even your portfolio rights."
        ),
        "standard_note": "⚠️ Non-standard: Most fair contracts allow you to keep IP, granting the client a license to use it.",
    },
    "Automatic Renewal": {
        "risk_level": "HIGH",
        "risk_score": 30,
        "icon": "🔴",
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "keywords": [
            "automatically renew", "auto-renew", "auto renew",
            "shall renew", "automatically extended", "unless terminated",
            "automatically continue", "successive terms",
        ],
        "simplify_hint": "automatic renewal and how to cancel",
        "why_it_matters": (
            "You could be locked into this contract renewals indefinitely "
            "unless you actively cancel before a deadline — which you might miss."
        ),
        "standard_note": "⚠️ Common but risky — always note the cancellation deadline.",
    },
    "Unilateral Termination": {
        "risk_level": "HIGH",
        "risk_score": 30,
        "icon": "🔴",
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "keywords": [
            "terminate at will", "terminate for any reason", "terminate without cause",
            "terminate upon notice", "convenience termination", "sole discretion",
            "may terminate", "right to terminate",
        ],
        "simplify_hint": "who can terminate the contract and under what conditions",
        "why_it_matters": (
            "The other party can end this contract at any time, for any reason, "
            "potentially leaving you without payment for work already completed."
        ),
        "standard_note": "⚠️ One-sided — a fair contract should require mutual grounds for termination.",
    },
    "Unlimited Liability": {
        "risk_level": "HIGH",
        "risk_score": 30,
        "icon": "🔴",
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "keywords": [
            "unlimited liability", "no cap", "no limitation on liability",
            "fully liable", "liable for all", "any and all damages",
            "consequential damages", "indirect damages", "lost profits",
        ],
        "simplify_hint": "limits on financial liability and damages",
        "why_it_matters": (
            "Without a liability cap, you could be held personally responsible "
            "for unlimited financial damages. This can exceed your contract value many times over."
        ),
        "standard_note": "🚨 High risk — always negotiate a liability cap equal to the contract value.",
    },
    "Non-Compete": {
        "risk_level": "HIGH",
        "risk_score": 25,
        "icon": "🔴",
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "keywords": [
            "non-compete", "noncompete", "non compete", "not compete",
            "compete with", "competitive activities", "similar services",
            "competing business", "competing products",
        ],
        "simplify_hint": "restrictions on working with competitors or in similar industries",
        "why_it_matters": (
            "This restricts your ability to work for similar clients or in the same industry, "
            "potentially blocking your primary source of income after this contract ends."
        ),
        "standard_note": "⚠️ Non-standard for freelance work — negotiate a limited scope and time period.",
    },
    "Indemnification": {
        "risk_level": "HIGH",
        "risk_score": 25,
        "icon": "🔴",
        "color": "#DC2626",
        "bg": "#FEE2E2",
        "keywords": [
            "indemnify", "indemnification", "hold harmless",
            "defend and indemnify", "indemnified party",
            "losses and damages", "third party claims", "defend against",
        ],
        "simplify_hint": "indemnification obligations and who pays for legal costs",
        "why_it_matters": (
            "You may be required to pay the other party's legal fees and damages "
            "if a third party files a claim against them — even if you're not at fault."
        ),
        "standard_note": "⚠️ Should be mutual — you should only indemnify for your own negligence.",
    },
    "Non-Solicitation": {
        "risk_level": "MEDIUM",
        "risk_score": 15,
        "icon": "🟡",
        "color": "#D97706",
        "bg": "#FEF3C7",
        "keywords": [
            "non-solicitation", "nonsolicitation", "not solicit",
            "do not solicit", "poach", "hire away", "recruit employees",
            "solicit customers", "solicit clients",
        ],
        "simplify_hint": "restrictions on recruiting staff or approaching clients",
        "why_it_matters": (
            "You may be prevented from hiring the client's employees or contacting "
            "their customers — even indirectly — for a set period after the contract ends."
        ),
        "standard_note": "✅ Common in professional contracts — check duration and scope.",
    },
    "Governing Law & Jurisdiction": {
        "risk_level": "MEDIUM",
        "risk_score": 15,
        "icon": "🟡",
        "color": "#D97706",
        "bg": "#FEF3C7",
        "keywords": [
            "governed by", "laws of", "jurisdiction", "governing law",
            "exclusive jurisdiction", "courts of", "state of", "laws of the state",
        ],
        "simplify_hint": "which country or state's laws apply and where disputes are decided",
        "why_it_matters": (
            "If a dispute arises, it must be resolved in the specified jurisdiction "
            "— traveling to another country for litigation is expensive and inconvenient."
        ),
        "standard_note": "ℹ️ Check whether the jurisdiction is practical for you.",
    },
    "Arbitration": {
        "risk_level": "MEDIUM",
        "risk_score": 15,
        "icon": "🟡",
        "color": "#D97706",
        "bg": "#FEF3C7",
        "keywords": [
            "arbitration", "arbitrate", "binding arbitration",
            "dispute resolution", "american arbitration", "aaa rules",
            "settled by arbitration", "arbitral tribunal",
        ],
        "simplify_hint": "dispute resolution process and whether court access is waived",
        "why_it_matters": (
            "You may waive your right to sue in a regular court and must instead "
            "use private arbitration — which can be expensive and favor larger parties."
        ),
        "standard_note": "⚠️ Check if arbitration costs are shared or borne by one party.",
    },
    "Limitation of Liability": {
        "risk_level": "MEDIUM",
        "risk_score": 10,
        "icon": "🟡",
        "color": "#D97706",
        "bg": "#FEF3C7",
        "keywords": [
            "limitation of liability", "limit liability", "cap on liability",
            "not liable for", "in no event", "maximum liability",
            "liability shall not exceed",
        ],
        "simplify_hint": "cap on financial liability and what damages can be claimed",
        "why_it_matters": (
            "Your ability to recover damages may be strictly capped — "
            "even if your actual losses far exceed the contract value."
        ),
        "standard_note": "✅ A mutual liability cap is standard and generally fair.",
    },
    "Confidentiality / NDA": {
        "risk_level": "MEDIUM",
        "risk_score": 10,
        "icon": "🟡",
        "color": "#D97706",
        "bg": "#FEF3C7",
        "keywords": [
            "confidential", "confidentiality", "non-disclosure", "nda",
            "trade secret", "proprietary information", "disclose",
            "keep confidential", "not disclose",
        ],
        "simplify_hint": "confidentiality obligations and what information must be kept secret",
        "why_it_matters": (
            "You are legally obligated to keep certain information secret. "
            "Violations can result in significant financial penalties, even unintentional ones."
        ),
        "standard_note": "✅ Standard clause — check duration and scope of confidential information.",
    },
    "Change of Control": {
        "risk_level": "MEDIUM",
        "risk_score": 10,
        "icon": "🟡",
        "color": "#D97706",
        "bg": "#FEF3C7",
        "keywords": [
            "change of control", "merger", "acquisition", "assigns to",
            "transfer agreement", "successor", "assign this agreement",
        ],
        "simplify_hint": "what happens if the company is sold or merged",
        "why_it_matters": (
            "If the company is acquired, your contract automatically transfers "
            "to the new owner — who may have very different expectations."
        ),
        "standard_note": "ℹ️ Consider negotiating a right to terminate upon change of control.",
    },
    "Payment Terms": {
        "risk_level": "LOW",
        "risk_score": 5,
        "icon": "🟢",
        "color": "#16A34A",
        "bg": "#DCFCE7",
        "keywords": [
            "payment", "invoice", "net 30", "net 60", "payable",
            "compensation", "fee", "rate", "per hour", "monthly fee",
            "due within", "payment schedule",
        ],
        "simplify_hint": "payment schedule, amounts, and invoicing process",
        "why_it_matters": "Understanding exactly when and how you'll be paid is critical for your cash flow.",
        "standard_note": "✅ Standard clause — confirm net days and accepted payment methods.",
    },
    "Effective Date & Term": {
        "risk_level": "LOW",
        "risk_score": 3,
        "icon": "🟢",
        "color": "#16A34A",
        "bg": "#DCFCE7",
        "keywords": [
            "effective date", "commencement date", "start date",
            "commencing on", "effective as of", "dated as of", "term of",
            "initial term", "agreement term",
        ],
        "simplify_hint": "when the contract starts and how long it lasts",
        "why_it_matters": "Confirms when your obligations begin and how long you're committed for.",
        "standard_note": "✅ Informational — confirms the contract timeline.",
    },
}

# ─── Sample Contract (for demo mode) ─────────────────────────────────────────
SAMPLE_CONTRACT = """
FREELANCE SERVICE AGREEMENT

This Freelance Service Agreement ("Agreement") is entered into as of April 1, 2026,
by and between TechCorp International LLC, a Delaware corporation ("Client"), and
the freelancer identified below ("Contractor").

1. SERVICES
Contractor agrees to provide software development services as specified in each
Statement of Work. Client may terminate this Agreement at any time, for any reason,
upon 7 days written notice to Contractor.

2. COMPENSATION
Client shall pay Contractor at a rate of $50 per hour. Invoices are due within
Net 60 days of receipt. Client reserves the right to dispute any invoice within
30 days.

3. INTELLECTUAL PROPERTY
All work product, inventions, code, designs, and deliverables created by Contractor
under this Agreement shall be considered "work for hire" and all right, title, and
interest in such work shall be exclusively owned by Client. Contractor hereby
irrevocably assigns all intellectual property rights to Client.

4. CONFIDENTIALITY
Contractor agrees to keep all Client information, trade secrets, and proprietary
data strictly confidential and shall not disclose any such information to third
parties during the term of this Agreement and for 5 years thereafter.

5. NON-COMPETE
For a period of 24 months following termination of this Agreement, Contractor shall
not engage in any business or activity that directly or indirectly competes with
Client's business in any market where Client operates.

6. NON-SOLICITATION
For 12 months after termination, Contractor shall not solicit or hire any of
Client's employees, contractors, or customers.

7. INDEMNIFICATION
Contractor shall indemnify, defend, and hold harmless Client and its officers,
directors, and employees from any and all claims, damages, losses, costs, and
expenses (including attorneys' fees) arising out of or related to Contractor's
performance under this Agreement.

8. LIABILITY
IN NO EVENT SHALL CLIENT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, CONSEQUENTIAL,
OR PUNITIVE DAMAGES. CONTRACTOR'S TOTAL LIABILITY TO CLIENT SHALL NOT EXCEED
THE FEES PAID IN THE PRIOR 30 DAYS. CONTRACTOR'S LIABILITY TO THIRD PARTIES
SHALL BE UNLIMITED.

9. GOVERNING LAW
This Agreement shall be governed by the laws of the State of Delaware, USA.
Any disputes shall be resolved exclusively in the courts of New Castle County,
Delaware, and Contractor irrevocably consents to such jurisdiction.

10. ARBITRATION
Any dispute, controversy, or claim arising out of or relating to this Agreement
shall be settled by binding arbitration under the rules of the American Arbitration
Association. The arbitration shall take place in Wilmington, Delaware.

11. AUTOMATIC RENEWAL
This Agreement shall automatically renew for successive one-year terms unless
either party provides written notice of non-renewal at least 60 days prior to
the end of the then-current term.

12. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement between the parties and supersedes
all prior negotiations, representations, or agreements.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first
written above.

TechCorp International LLC                    Contractor
By: ___________________________               By: ___________________________
Name: John Smith, CEO                         Name:
Date:                                         Date:
"""
