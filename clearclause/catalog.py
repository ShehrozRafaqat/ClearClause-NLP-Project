"""Clause catalog used by the hybrid NLP extractor.

The rules are intentionally transparent for a classroom demo: each detected
clause can be traced back to explicit legal patterns plus semantic prototypes.
Every rule also carries a *fair standard* (what a balanced version of the clause
looks like) and concrete *negotiation actions* so the UI can coach the user
through the contract, not just flag risk.
"""

from __future__ import annotations

from .models import ClauseRule


SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}

SEVERITY_TONES = {
    "HIGH": "#c2410c",
    "MEDIUM": "#b45309",
    "LOW": "#15803d",
    "INFO": "#2563eb",
}

DIMENSIONS = {
    "money": "Money exposure",
    "ownership": "Ownership and data",
    "freedom": "Work freedom",
    "disputes": "Disputes and enforcement",
    "operations": "Operational clarity",
}

CATEGORY_ORDER = [
    "Ownership & IP",
    "Money & Liability",
    "Termination & Renewal",
    "Work Freedom",
    "Disputes",
    "Data & Compliance",
    "Operations",
]


CLAUSE_RULES: list[ClauseRule] = [
    ClauseRule(
        clause_id="ip_ownership",
        title="IP Ownership / Work-for-Hire",
        severity="HIGH",
        base_weight=22,
        dimension="ownership",
        category="Ownership & IP",
        patterns=[
            r"\bwork[- ]?for[- ]?hire\b",
            r"\bintellectual property\b",
            r"\ball rights?,\s*title(,\s*and)? interest\b",
            r"\birrevocably assigns?\b",
            r"\bassigns?\s+all(?:\s+\S+){0,4}?\s+rights?\b",
            r"\bassigns?\s+all\s+right(?:s)?,",
            r"\bowned exclusively by\b",
            r"\bperpetual,?\s+irrevocable\b",
        ],
        prototypes=[
            "ownership of deliverables, work product, source code, designs and inventions",
            "contractor assigns intellectual property rights to client",
            "client receives broad license or exclusive ownership of created work",
        ],
        red_flags=[r"\birrevocably\b", r"\bexclusive(?:ly)? owned\b", r"\ball right"],
        green_flags=[r"\bportfolio\b", r"\bpre[- ]existing\b", r"\blicense\b"],
        why_it_matters=(
            "This controls who owns the work after delivery. For freelancers, losing all IP "
            "can also mean losing reuse rights, portfolio rights, and reusable code libraries."
        ),
        business_impact=(
            "Directly affects future income because the freelancer may be blocked from reusing "
            "similar work for other clients."
        ),
        recommendation=(
            "Ask for clear carve-outs for pre-existing tools, learning material, templates, "
            "and portfolio display rights."
        ),
        plain_template=(
            "This part is about who owns the work you create. The detected language suggests "
            "the client may receive broad ownership or control over the deliverables."
        ),
        questions=[
            "Who owns the final work and source files?",
            "Can I reuse my own templates or reusable code later?",
            "Can I show this project in my portfolio?",
        ],
        fair_standard=(
            "Client receives a license (or assignment of the final deliverables) only after full "
            "payment. Contractor retains pre-existing tools, templates, generic libraries, and "
            "portfolio display rights for non-confidential work."
        ),
        negotiation_actions=[
            "Carve out pre-existing tools, templates, and generic libraries from the assignment",
            "Make the IP assignment effective only on final payment, not at signing",
            "Reserve portfolio display rights for non-confidential portions of the work",
        ],
    ),
    ClauseRule(
        clause_id="unlimited_liability",
        title="Unlimited Liability",
        severity="HIGH",
        base_weight=24,
        dimension="money",
        category="Money & Liability",
        patterns=[
            r"\bunlimited liability\b",
            r"\bno limitation on liability\b",
            r"\bliable for any and all\b",
            r"\bany and all damages\b",
            r"\bconsequential damages\b",
            r"\bindirect damages\b",
            r"\blost profits\b",
            r"\bliability .* shall be unlimited\b",
        ],
        prototypes=[
            "unlimited financial responsibility for damages losses costs expenses",
            "no cap on contractor liability and exposure to consequential damages",
            "freelancer may pay more than the contract value if something goes wrong",
        ],
        red_flags=[r"\bunlimited\b", r"\bconsequential damages\b", r"\blost profits\b"],
        green_flags=[r"\bliability .* shall not exceed\b", r"\bcap(?:ped)? at\b", r"\bfees paid\b"],
        why_it_matters=(
            "Without a fair liability cap, a small contract can create a much larger financial "
            "risk than the freelancer can realistically afford."
        ),
        business_impact=(
            "A single dispute could exceed the project fee and create personal financial exposure."
        ),
        recommendation=(
            "Negotiate a mutual cap, usually limited to fees paid under the contract, and exclude "
            "indirect or consequential damages."
        ),
        plain_template=(
            "This part may make you financially responsible for very large losses. A safer version "
            "would cap liability to a predictable amount."
        ),
        questions=[
            "Is my liability capped?",
            "Can the client claim indirect losses or lost profits?",
            "Is the liability cap mutual for both parties?",
        ],
        fair_standard=(
            "Liability is mutually capped (commonly 12 months of fees, or the contract value). "
            "Indirect, consequential, punitive, and lost-profit damages are excluded on both sides, "
            "with narrow carve-outs only for gross negligence or wilful misconduct."
        ),
        negotiation_actions=[
            "Add a mutual liability cap equal to fees paid in the prior 12 months",
            "Exclude indirect, consequential, punitive, and lost-profit damages for both parties",
            "Limit any 'unlimited' carve-outs to gross negligence or wilful misconduct",
        ],
    ),
    ClauseRule(
        clause_id="indemnification",
        title="Indemnification",
        severity="HIGH",
        base_weight=20,
        dimension="money",
        category="Money & Liability",
        patterns=[
            r"\bindemnif(?:y|ication)\b",
            r"\bhold harmless\b",
            r"\bdefend and indemnify\b",
            r"\bthird[- ]party claims?\b",
            r"\battorneys?' fees\b",
            r"\blosses,? damages,? costs\b",
        ],
        prototypes=[
            "contractor must defend indemnify and hold harmless client from claims losses damages fees",
            "freelancer pays legal costs if a third party claim is made",
        ],
        red_flags=[r"\bdefend\b", r"\bhold harmless\b", r"\battorneys?' fees\b"],
        green_flags=[r"\bto the extent caused by\b", r"\bgross negligence\b", r"\bmutual indemn"],
        why_it_matters=(
            "Indemnity can shift legal costs from the client to the freelancer, sometimes even "
            "before fault is clearly proven."
        ),
        business_impact=(
            "Legal-defense costs can be much higher than the project value."
        ),
        recommendation=(
            "Limit indemnity to claims caused by your own breach, negligence, or IP infringement, "
            "and make the obligation mutual where appropriate."
        ),
        plain_template=(
            "This part can require you to pay for claims or legal costs connected to the project. "
            "It should be limited to problems you actually caused."
        ),
        questions=[
            "Do I have to pay the client's legal fees?",
            "Is indemnity limited to my own mistakes?",
            "Is the indemnity obligation mutual?",
        ],
        fair_standard=(
            "Indemnity is mutual and only applies 'to the extent caused by' the indemnifier's own "
            "breach, gross negligence, or IP infringement. Defense costs are not advanced before "
            "fault is established."
        ),
        negotiation_actions=[
            "Make indemnity mutual: each party covers claims it actually caused",
            "Limit the trigger to 'to the extent caused by' your own breach, negligence, or IP claim",
            "Require the client to control defense and let you approve any settlement",
        ],
    ),
    ClauseRule(
        clause_id="unilateral_termination",
        title="Unilateral Termination",
        severity="HIGH",
        base_weight=19,
        dimension="freedom",
        category="Termination & Renewal",
        patterns=[
            r"\bterminate .* for any reason\b",
            r"\bterminate .* without cause\b",
            r"\bterminate .* at (?:its|their|client'?s) convenience\b",
            r"\bsole discretion\b",
            r"\bmay terminate .* upon .* notice\b",
            r"\bright to terminate\b",
        ],
        prototypes=[
            "client may terminate agreement at any time for any reason without cause",
            "one party can end the contract on short notice",
        ],
        red_flags=[r"\bfor any reason\b", r"\bwithout cause\b", r"\bsole discretion\b"],
        green_flags=[r"\bmutual\b", r"\bfor cause\b", r"\bpayment for work performed\b"],
        why_it_matters=(
            "If only the client can end the contract freely, the freelancer may lose expected "
            "income after already reserving time or starting work."
        ),
        business_impact=(
            "Creates unstable revenue and weakens negotiation power."
        ),
        recommendation=(
            "Ask for payment for completed work, a kill fee, notice period, and mutual termination rights."
        ),
        plain_template=(
            "This part may let the client end the contract quickly or without a strong reason. "
            "You should check whether completed work must still be paid."
        ),
        questions=[
            "Can the client terminate me without cause?",
            "How many days of notice are required?",
            "Will I be paid for work already completed?",
        ],
        fair_standard=(
            "Termination rights are mutual. For-convenience termination requires 14-30 days' "
            "written notice and the client must pay for all work performed plus approved expenses "
            "through the termination date."
        ),
        negotiation_actions=[
            "Make the termination right mutual — either party may exit on the same notice",
            "Require 14-30 days' written notice instead of immediate termination",
            "Require payment for all work performed and a kill fee on for-convenience termination",
        ],
    ),
    ClauseRule(
        clause_id="non_compete",
        title="Non-Compete",
        severity="HIGH",
        base_weight=20,
        dimension="freedom",
        category="Work Freedom",
        patterns=[
            r"\bnon[- ]?compete\b",
            r"\bnot compete\b",
            r"\bcompetitive activit(?:y|ies)\b",
            r"\bcompeting\s+(?:business|product|brand|service|company|beverage|good)\w*\b",
            r"\bsimilar services\b",
            r"\brestricted business\b",
            r"\bshall not\s+(?:promote|endorse|provide|engage in|appear in)\b",
        ],
        prototypes=[
            "freelancer cannot work with competitors or similar businesses after contract ends",
            "restriction on providing similar services in the same market",
        ],
        red_flags=[r"\b24 months\b", r"\btwo years\b", r"\bany market\b", r"\bworldwide\b"],
        green_flags=[r"\bdirect competitors\b", r"\b6 months\b", r"\bspecific client\b"],
        why_it_matters=(
            "A broad non-compete can stop a freelancer from accepting future work in their own field."
        ),
        business_impact=(
            "May block the freelancer's main source of income after the project."
        ),
        recommendation=(
            "Remove it if possible. If not, narrow it by time, geography, client list, and exact services."
        ),
        plain_template=(
            "This part restricts who you can work for after this contract. Broad wording can damage "
            "your ability to earn from similar clients."
        ),
        questions=[
            "Am I allowed to work for similar clients?",
            "How long does the restriction last?",
            "Which competitors or markets are actually covered?",
        ],
        fair_standard=(
            "If a non-compete is needed at all, it is narrow: limited to a short, named list of "
            "direct competitors, lasts 6-12 months, and applies only to the specific services and "
            "geographies the client actually operates in."
        ),
        negotiation_actions=[
            "Push to remove the non-compete entirely or convert it to a non-solicit",
            "Cap the duration at 6 to 12 months post-termination",
            "Narrow it to a named, finite list of direct competitors and the markets actually served",
        ],
    ),
    ClauseRule(
        clause_id="automatic_renewal",
        title="Automatic Renewal",
        severity="HIGH",
        base_weight=17,
        dimension="freedom",
        category="Termination & Renewal",
        patterns=[
            r"\bautomatically renew(?:s|ed)?\b",
            r"\bauto[- ]?renew\b",
            r"\bautomatically extended\b",
            r"\bsuccessive terms\b",
            r"\bunless .* notice of non[- ]renewal\b",
        ],
        prototypes=[
            "contract renews automatically unless notice is given before deadline",
            "successive renewal terms and cancellation window",
        ],
        red_flags=[r"\b60 days\b", r"\b90 days\b", r"\bone-year terms\b"],
        green_flags=[r"\b30 days\b", r"\bwritten notice at any time\b"],
        why_it_matters=(
            "Automatic renewal can lock a freelancer into a contract if the cancellation window is missed."
        ),
        business_impact=(
            "Can create unwanted ongoing obligations or missed renegotiation opportunities."
        ),
        recommendation=(
            "Calendar the non-renewal deadline and ask for a shorter notice window."
        ),
        plain_template=(
            "This part can renew the contract automatically. You need to know the exact deadline "
            "for sending cancellation notice."
        ),
        questions=[
            "Does the contract renew automatically?",
            "What is the cancellation deadline?",
            "How long is each renewal term?",
        ],
        fair_standard=(
            "Either (a) the contract does not auto-renew, or (b) it renews for short terms with a "
            "short notice window (e.g. 30 days) and the renewing party must send a renewal reminder."
        ),
        negotiation_actions=[
            "Replace auto-renewal with an opt-in renewal letter signed by both parties",
            "Shorten the non-renewal notice window to 30 days or less",
            "Require the client to send a written renewal reminder 45 days before renewal",
        ],
    ),
    ClauseRule(
        clause_id="exclusivity",
        title="Exclusivity",
        severity="HIGH",
        base_weight=17,
        dimension="freedom",
        category="Work Freedom",
        patterns=[
            r"\bexclusiv(?:e|ely|ity)\b",
            r"\bsole provider\b",
            r"\bshall not provide services\b",
            r"\bno other clients\b",
            r"\bexclusive arrangement\b",
            r"\bcategory exclusivity\b",
        ],
        prototypes=[
            "freelancer must work exclusively for client and cannot serve other clients",
            "exclusive services arrangement limits outside work",
        ],
        red_flags=[r"\bno other clients\b", r"\bexclusive basis\b", r"\bworldwide\b"],
        green_flags=[r"\bproject-specific\b", r"\bduring working hours\b"],
        why_it_matters=(
            "Exclusivity limits the freelancer's ability to earn from other clients while the contract runs."
        ),
        business_impact=(
            "Can reduce revenue diversification and make the freelancer dependent on one client."
        ),
        recommendation=(
            "Tie exclusivity to a specific project, paid retainer, or narrow conflict category."
        ),
        plain_template=(
            "This part may limit your ability to work for other clients. It should be narrow and "
            "matched with fair compensation."
        ),
        questions=[
            "Can I serve other clients during this contract?",
            "Is exclusivity limited to direct competitors?",
            "Am I paid enough to justify exclusivity?",
        ],
        fair_standard=(
            "Exclusivity is tied to a paid retainer or a specific project. It excludes general "
            "industry work and only blocks direct competitors of the client by name."
        ),
        negotiation_actions=[
            "Replace blanket exclusivity with a named conflict-of-interest list",
            "Tie exclusivity to a paid retainer that compensates lost outside revenue",
            "Limit exclusivity to working hours dedicated to the project",
        ],
    ),
    ClauseRule(
        clause_id="payment_terms",
        title="Payment Terms",
        severity="LOW",
        base_weight=7,
        dimension="money",
        category="Money & Liability",
        patterns=[
            r"\bpayment\b",
            r"\binvoice\b",
            r"\bnet\s*(?:15|30|45|60|90)\b",
            r"\bpayable\b",
            r"\bcompensation\b",
            r"\bfee\b",
            r"\brate\b",
            r"\bdue within\b",
        ],
        prototypes=[
            "payment schedule invoice due date compensation fee hourly rate milestone payment",
            "how and when freelancer gets paid",
        ],
        red_flags=[r"\bnet\s*(?:60|90)\b", r"\bdispute any invoice\b", r"\bwithhold payment\b"],
        green_flags=[r"\bnet\s*(?:7|15|30)\b", r"\bmilestone\b", r"\badvance\b"],
        why_it_matters=(
            "Payment language decides when money arrives and what the client can dispute or withhold."
        ),
        business_impact=(
            "Slow or unclear payment terms can create cash-flow problems."
        ),
        recommendation=(
            "Prefer milestone payments, deposits, late-fee language, and a short invoice period."
        ),
        plain_template=(
            "This part explains when and how you get paid. Watch for long payment windows or broad "
            "invoice dispute rights."
        ),
        questions=[
            "When will invoices be paid?",
            "Can the client dispute or withhold payment?",
            "Are milestone payments or deposits included?",
        ],
        fair_standard=(
            "An upfront deposit (20-30%) plus milestone or Net 15 payments. Disputes apply only to "
            "the disputed portion of an invoice — undisputed amounts must be paid on schedule. "
            "Late fees apply after a short grace period."
        ),
        negotiation_actions=[
            "Move payment to Net 15 (or milestone-based) with a 20-30% upfront deposit",
            "Limit dispute rights to the specific disputed line item, not the entire invoice",
            "Add a 1.5%/month late fee after a short grace period",
        ],
    ),
    ClauseRule(
        clause_id="confidentiality",
        title="Confidentiality / NDA",
        severity="MEDIUM",
        base_weight=11,
        dimension="ownership",
        category="Ownership & IP",
        patterns=[
            r"\bconfidential(?:ity)?\b",
            r"\bnon[- ]disclosure\b",
            r"\bNDA\b",
            r"\btrade secrets?\b",
            r"\bproprietary information\b",
            r"\bnot disclose\b",
        ],
        prototypes=[
            "confidential information trade secrets proprietary data not disclose",
            "non-disclosure obligations continue after contract ends",
        ],
        red_flags=[r"\bperpetual\b", r"\b5 years\b", r"\bindefinite\b"],
        green_flags=[r"\bpublicly available\b", r"\balready known\b", r"\brequired by law\b"],
        why_it_matters=(
            "Confidentiality is normal, but broad or indefinite wording can create accidental breach risk."
        ),
        business_impact=(
            "May limit portfolio use, marketing, and discussion of prior experience."
        ),
        recommendation=(
            "Make sure common exceptions are included and the duration is reasonable."
        ),
        plain_template=(
            "This part requires you to keep client information private. Check how long it lasts and "
            "whether normal exceptions are included."
        ),
        questions=[
            "What information is confidential?",
            "How long does confidentiality last?",
            "Can I mention the client or project in my portfolio?",
        ],
        fair_standard=(
            "Confidentiality lasts 2-3 years (longer only for trade secrets), is mutual, and "
            "excludes publicly available, already-known, independently-developed, or legally "
            "compelled information."
        ),
        negotiation_actions=[
            "Cap the confidentiality period at 2-3 years for ordinary information",
            "Add standard exceptions: public, already known, independently developed, required by law",
            "Reserve the right to list the client and a generic project description in your portfolio",
        ],
    ),
    ClauseRule(
        clause_id="non_solicitation",
        title="Non-Solicitation",
        severity="MEDIUM",
        base_weight=10,
        dimension="freedom",
        category="Work Freedom",
        patterns=[
            r"\bnon[- ]?solicitation\b",
            r"\bnot solicit\b",
            r"\bsolicit .* customers?\b",
            r"\bsolicit .* employees?\b",
            r"\bhire away\b",
            r"\bpoach\b",
        ],
        prototypes=[
            "cannot solicit hire recruit employees customers contractors after termination",
            "restriction on approaching client's staff or customers",
        ],
        red_flags=[r"\b24 months\b", r"\ball customers\b", r"\bindirectly\b"],
        green_flags=[r"\b12 months\b", r"\bwith whom .* had contact\b"],
        why_it_matters=(
            "This can restrict business development after the contract, especially if the client has "
            "a broad customer network."
        ),
        business_impact=(
            "Can limit future clients, partnerships, or hiring opportunities."
        ),
        recommendation=(
            "Limit it to direct contacts from the project and a short duration."
        ),
        plain_template=(
            "This part limits whether you can approach the client's employees or customers. It should "
            "only cover people you actually worked with."
        ),
        questions=[
            "Who am I restricted from contacting?",
            "How long does the restriction last?",
            "Does it cover indirect contact too?",
        ],
        fair_standard=(
            "Limited to people you actually worked with during the engagement and capped at 12 months. "
            "Excludes general industry contact, public job posts, and responses to inbound inquiries."
        ),
        negotiation_actions=[
            "Limit the restriction to people you actually had project contact with",
            "Cap the duration at 12 months post-termination",
            "Exclude general job postings and inbound inquiries from the restriction",
        ],
    ),
    ClauseRule(
        clause_id="governing_law",
        title="Governing Law & Jurisdiction",
        severity="MEDIUM",
        base_weight=10,
        dimension="disputes",
        category="Disputes",
        patterns=[
            r"\bgoverned by\b",
            r"\blaws of\b",
            r"\bjurisdiction\b",
            r"\bexclusive jurisdiction\b",
            r"\bcourts of\b",
            r"\bvenue\b",
        ],
        prototypes=[
            "which country's law applies and where disputes must be filed",
            "exclusive jurisdiction courts venue governing law",
        ],
        red_flags=[r"\bexclusive jurisdiction\b", r"\birrevocably consents\b", r"\bforeign\b"],
        green_flags=[
            r"\bmutual agreement\b",
            r"\bwhere(?:\s+the)?\s+contractor\s+resides\b",
            r"\bgood[- ]faith negotiation\b",
        ],
        why_it_matters=(
            "A far-away court or foreign jurisdiction can make dispute resolution expensive and impractical."
        ),
        business_impact=(
            "Raises enforcement cost and can discourage the freelancer from pursuing unpaid invoices."
        ),
        recommendation=(
            "Prefer neutral online dispute resolution, local jurisdiction, or clear arbitration cost rules."
        ),
        plain_template=(
            "This part says which law applies and where disputes must be handled. A distant location "
            "can make enforcement expensive."
        ),
        questions=[
            "Which law governs the contract?",
            "Where would a dispute be heard?",
            "Would travel or foreign legal costs be required?",
        ],
        fair_standard=(
            "A neutral or mutually convenient jurisdiction. Many freelance contracts use online "
            "dispute resolution or small-claims court for low-value invoice disputes."
        ),
        negotiation_actions=[
            "Move jurisdiction to your home country or a neutral online dispute platform",
            "Preserve the right to use small-claims court for unpaid invoices",
            "Add a 'good faith negotiation' step before formal litigation",
        ],
    ),
    ClauseRule(
        clause_id="arbitration",
        title="Arbitration / Court Waiver",
        severity="MEDIUM",
        base_weight=10,
        dimension="disputes",
        category="Disputes",
        patterns=[
            r"\barbitration\b",
            r"\barbitrate\b",
            r"\bbinding arbitration\b",
            r"\bdispute resolution\b",
            r"\bclass action waiver\b",
            r"\bwaive .* jury\b",
        ],
        prototypes=[
            "binding arbitration instead of court dispute resolution waiver",
            "private arbitration rules costs and venue",
        ],
        red_flags=[r"\bbinding\b", r"\bclass action waiver\b", r"\bclient'?s location\b"],
        green_flags=[r"\bcosts shared equally\b", r"\bonline arbitration\b", r"\bsmall claims\b"],
        why_it_matters=(
            "Arbitration can be faster, but it may also be costly and remove normal court options."
        ),
        business_impact=(
            "May make small invoice disputes uneconomical to pursue."
        ),
        recommendation=(
            "Clarify arbitration cost sharing, location, and whether small claims remain available."
        ),
        plain_template=(
            "This part may require disputes to go through private arbitration instead of court. "
            "Check who pays and where it happens."
        ),
        questions=[
            "Do I have to arbitrate instead of going to court?",
            "Who pays arbitration costs?",
            "Is small-claims court still allowed?",
        ],
        fair_standard=(
            "Arbitration costs are shared (or paid by the party initiating), the venue is online or "
            "mutually convenient, and small-claims court remains available for low-value disputes."
        ),
        negotiation_actions=[
            "Carve out small-claims court for unpaid invoices below a threshold",
            "Require arbitration costs to be shared equally (or follow loser-pays)",
            "Choose an online arbitration provider so travel is not required",
        ],
    ),
    ClauseRule(
        clause_id="liability_cap",
        title="Limitation of Liability",
        severity="MEDIUM",
        base_weight=8,
        dimension="money",
        category="Money & Liability",
        patterns=[
            r"\blimitation of liability\b",
            r"\bliability shall not exceed\b",
            r"\bmaximum liability\b",
            r"\bcap on liability\b",
            r"\bin no event shall\b",
            r"\bnot liable for\b",
        ],
        prototypes=[
            "liability cap maximum amount recoverable damages limitation",
            "limits financial responsibility and excludes indirect damages",
        ],
        red_flags=[r"\bclient .* not liable\b", r"\bcontractor .* unlimited\b"],
        green_flags=[r"\bmutual\b", r"\bfees paid\b", r"\bcontract value\b"],
        why_it_matters=(
            "Liability caps are useful when mutual, but unfair when they protect only the stronger party."
        ),
        business_impact=(
            "Can reduce the client's responsibility while leaving the freelancer exposed."
        ),
        recommendation=(
            "Check whether the cap protects both parties equally and whether exceptions are reasonable."
        ),
        plain_template=(
            "This part limits how much one party can recover if something goes wrong. It should be "
            "mutual, balanced, and easy to calculate."
        ),
        questions=[
            "Is the liability cap mutual?",
            "What amount is the cap based on?",
            "Are any damages excluded?",
        ],
        fair_standard=(
            "The cap applies symmetrically to both parties, is anchored to a clear figure (fees in "
            "the prior 12 months or the contract value), and carve-outs are limited to wilful "
            "misconduct or IP infringement."
        ),
        negotiation_actions=[
            "Make the liability cap mutual — same number for both sides",
            "Anchor the cap to a clear, calculable amount (12 months of fees, or contract value)",
            "Narrow any 'uncapped' carve-outs to wilful misconduct or IP infringement",
        ],
    ),
    ClauseRule(
        clause_id="assignment_change",
        title="Assignment / Change of Control",
        severity="MEDIUM",
        base_weight=8,
        dimension="operations",
        category="Operations",
        patterns=[
            r"\bassign(?:s|ment)? this agreement\b",
            r"\bchange of control\b",
            r"\bmerger\b",
            r"\bacquisition\b",
            r"\bsuccessors and assigns\b",
            r"\btransfer this agreement\b",
        ],
        prototypes=[
            "contract may be assigned transferred to successor merger acquisition",
            "new company can inherit the agreement after change of control",
        ],
        red_flags=[r"\bwithout consent\b", r"\bsole discretion\b"],
        green_flags=[r"\bprior written consent\b", r"\bnot unreasonably withheld\b"],
        why_it_matters=(
            "Assignment can move the contract to a new company with different priorities or risk profile."
        ),
        business_impact=(
            "The freelancer may end up working for or enforcing payment against an unexpected party."
        ),
        recommendation=(
            "Require notice and consent before assignment, except for reasonable business transfers."
        ),
        plain_template=(
            "This part controls whether the contract can be transferred to another company. You should "
            "know whether your consent is required."
        ),
        questions=[
            "Can the client transfer this contract without asking me?",
            "What happens if the client is acquired?",
            "Do I have a right to terminate after assignment?",
        ],
        fair_standard=(
            "Assignment requires prior written consent, not to be unreasonably withheld. After a "
            "change of control, the non-assigning party may terminate within 30 days without penalty."
        ),
        negotiation_actions=[
            "Require prior written consent for any assignment",
            "Add a 30-day termination right after change of control",
            "Make the assignment clause mutual instead of one-sided",
        ],
    ),
    ClauseRule(
        clause_id="data_privacy",
        title="Data Privacy / Security",
        severity="MEDIUM",
        base_weight=9,
        dimension="ownership",
        category="Data & Compliance",
        patterns=[
            r"\bpersonal data\b",
            r"\bdata protection\b",
            r"\bsecurity breach\b",
            r"\bprivacy laws?\b",
            r"\bGDPR\b",
            r"\bdata processing\b",
            r"\bcybersecurity\b",
        ],
        prototypes=[
            "personal data privacy law security breach data processing cybersecurity",
            "obligations to protect customer data and report incidents",
        ],
        red_flags=[r"\bstrict liability\b", r"\bimmediate notice\b", r"\bpenalties\b"],
        green_flags=[r"\breasonable safeguards\b", r"\bmutual cooperation\b"],
        why_it_matters=(
            "Data obligations can create serious compliance duties even for small freelance projects."
        ),
        business_impact=(
            "A breach or privacy mistake can damage reputation and create legal cost."
        ),
        recommendation=(
            "Clarify what data is handled, required safeguards, breach notice timing, and liability cap."
        ),
        plain_template=(
            "This part covers personal data or security duties. Make sure the required safeguards are "
            "specific and realistic for the project."
        ),
        questions=[
            "What personal data will I handle?",
            "What security controls are required?",
            "What happens if there is a data breach?",
        ],
        fair_standard=(
            "Specific safeguards (encryption in transit, least-privilege access, breach notice within "
            "72 hours), mutual cooperation on incident response, and breach liability subject to the "
            "general liability cap."
        ),
        negotiation_actions=[
            "Replace 'immediate notice' with a 48-72 hour breach notification window",
            "Bring breach-related liability under the general mutual liability cap",
            "Require the client to provide a data processing addendum listing the data and purposes",
        ],
    ),
    ClauseRule(
        clause_id="scope_acceptance",
        title="Scope, Acceptance & Revisions",
        severity="LOW",
        base_weight=6,
        dimension="operations",
        category="Operations",
        patterns=[
            r"\bscope of work\b",
            r"\bstatement of work\b",
            r"\bdeliverables?\b",
            r"\bacceptance\b",
            r"\brevisions?\b",
            r"\bchange request\b",
        ],
        prototypes=[
            "deliverables scope of work acceptance criteria revisions change requests",
            "what freelancer must deliver and how client approves the work",
        ],
        red_flags=[r"\bunlimited revisions\b", r"\bsole satisfaction\b", r"\bwithout additional fee\b"],
        green_flags=[r"\bwritten change request\b", r"\bacceptance criteria\b", r"\badditional fees\b"],
        why_it_matters=(
            "A vague scope can cause unpaid extra work, delayed acceptance, or endless revisions."
        ),
        business_impact=(
            "Poor scope control leads to scope creep and lower project profit."
        ),
        recommendation=(
            "Define deliverables, acceptance criteria, revision limits, and paid change requests."
        ),
        plain_template=(
            "This part defines what you must deliver and how revisions are handled. Clear limits protect "
            "you from unpaid extra work."
        ),
        questions=[
            "What exact deliverables are required?",
            "How many revisions are included?",
            "What counts as final acceptance?",
        ],
        fair_standard=(
            "Each deliverable has named acceptance criteria, a fixed number of included revisions, "
            "and a written change-request process with additional fees for out-of-scope work."
        ),
        negotiation_actions=[
            "List specific, testable acceptance criteria for each deliverable",
            "Cap included revisions at a fixed number (e.g., 2 per deliverable)",
            "Require written change requests with quoted fees for anything out of scope",
        ],
    ),
    ClauseRule(
        clause_id="term_effective_date",
        title="Effective Date & Term",
        severity="INFO",
        base_weight=2,
        dimension="operations",
        category="Operations",
        patterns=[
            r"\beffective date\b",
            r"\bcommencement date\b",
            r"\bterm of\b",
            r"\binitial term\b",
            r"\bexpires?\b",
            r"\bdated as of\b",
        ],
        prototypes=[
            "effective date commencement date initial term expiration contract duration",
            "when the agreement starts and how long it lasts",
        ],
        red_flags=[],
        green_flags=[],
        why_it_matters=(
            "The term tells you when obligations begin, expire, or renew."
        ),
        business_impact=(
            "Useful for planning work, payment, and cancellation dates."
        ),
        recommendation=(
            "Confirm start date, end date, renewal deadline, and survival obligations."
        ),
        plain_template=(
            "This part establishes when the contract starts and how long it remains active."
        ),
        questions=[
            "When does the contract start?",
            "When does it expire?",
            "Which obligations survive after termination?",
        ],
        fair_standard=(
            "Clear start and end dates, a defined initial term, and an explicit list of obligations "
            "(confidentiality, IP assignment, payment for completed work) that survive termination."
        ),
        negotiation_actions=[
            "Confirm an unambiguous start date and an explicit end date",
            "List which obligations survive termination (and for how long)",
            "Sync the term length to your project plan and invoicing cycle",
        ],
    ),
]


RULE_BY_ID = {rule.clause_id: rule for rule in CLAUSE_RULES}


DEFAULT_QUESTIONS = [
    "What are the top risks in this contract?",
    "Who owns the final work?",
    "Can the client terminate without cause?",
    "When and how will I be paid?",
    "Are there any restrictions on future work?",
    "Is my liability capped?",
    "Does the contract renew automatically?",
]
