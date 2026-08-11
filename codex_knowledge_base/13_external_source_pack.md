# Heyup Affiliate Project — External Source Pack (v2)

This pack is prepared for uploading into a ChatGPT Project as external knowledge for the Heyup affiliate-content initiative.

Goal:
Build a scalable affiliate-content engine inside Heyup’s Newsroom and adjacent content surfaces, focused on tech and consumer electronics, while staying compliant with affiliate-disclosure rules and aligned with Google’s quality and structured-data guidance.

How to use this pack:
- Upload this markdown file into the ChatGPT Project as a knowledge file.
- Keep `14_external_sources_catalog.csv` as a lightweight tracking sheet for teammates.
- Treat the official platform/operator sources as the source of truth for implementation.

---

## Group A — Reference Site Samples

### 1) TOProductsReviews homepage
**URL:** https://toproductsreviews.com/

**Why keep it in the project**
- Good example of a commerce-content site organized around categories, blog content, and deals.
- Useful for studying high-level IA and the way “shopping blog” content supports affiliate intent.

**What to learn**
- Top-level navigation pattern: Categories / Online Shopping Blog / Today's Deals.
- Mix of evergreen categories and timely commerce posts.
- Signals that the site is commerce-led rather than news-led.

**Notes**
- Homepage describes itself as “America's Top Review Platform.”
- It says it uses extensive online data processing to provide product comparisons and reviews.
- It prominently features deal/news-style posts and category navigation.

---

### 2) BestProductsReviews homepage
**URL:** https://www.bestproductsreviews.com/

**Why keep it in the project**
- Clear example of a comparison-first affiliate content property.
- Useful for understanding disclosure, ranking explanation, and category coverage.

**What to learn**
- Homepage language explains that rankings are generated from analysis of customer reviews, brands, merchant customer service, popularity trends, and more.
- It places “Advertising Disclosure” near its ranking explanation.
- It mixes comparison pages, category hubs, and blog/deal content.

**Notes**
- Useful benchmark for how to explain ranking logic without exposing internal implementation.
- Good reference for “popular comparisons” and category expansion ideas.

---

### 3) BestChoice comparison page sample
**URL:** https://www.bestchoice.com/comparison/laptop

**Why keep it in the project**
- Strong example of a month-based comparison landing page.
- Useful for recurring refreshable formats like “[category] comparison - [month year]”.

**What to learn**
- Date-stamped comparison pattern with “Last Updated”.
- Comparison pages can be designed as refreshable landing pages rather than one-off articles.
- Commercial/disclosure language is embedded directly into the comparison experience.

**Notes**
- Especially useful for Heyup pages like “Laptop Comparison - March 2026” or “Best Headphones - 2026”.

---

## Group B — Affiliate / Disclosure / Review Compliance

### 4) Amazon Associates disclosure guidance
**URL:** https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE

**Why keep it in the project**
- This is one of the most important operating constraints for Heyup affiliate content.
- It defines what Amazon expects from affiliates around disclosure.

**What to learn**
- Amazon requires a legally compliant link-level disclosure.
- Amazon also requires the site-level statement: “As an Amazon Associate I earn from qualifying purchases.”
- Link-level disclosure examples include “(paid link)”, “#ad”, and “#CommissionsEarned”.
- Disclosure must be near affiliate links and easy for customers to notice.

**Implementation impact**
- Every template that contains affiliate links should have:
  - site-level disclosure support
  - link-level disclosure support
  - a reusable disclosure component

---

### 5) FTC endorsement and review guidance
**URL:** https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking

**Why keep it in the project**
- FTC guidance is the general disclosure baseline beyond any one affiliate network.
- It matters for article templates, social distribution, and any creator/editor workflow.

**What to learn**
- Disclosures should be clear and conspicuous.
- The closer the disclosure is to the recommendation, the better.
- Hyperlinked disclosures alone are not enough if users can easily miss them.
- Each ad or endorsement that needs disclosure should carry it clearly on its own.

**Implementation impact**
- Do not hide disclosure behind tooltips or hard-to-see links.
- Avoid disclosure patterns that rely on users clicking elsewhere.

---

## Group C — Google Search Quality & Structured Data

### 6) Google: Write high quality reviews
**URL:** https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews

**Why keep it in the project**
- This should guide content quality requirements for any affiliate/review/comparison workflow.

**What to learn**
- Google recommends evaluating from a user’s perspective.
- Show expertise and first-hand knowledge where possible.
- Provide evidence, measurements, differentiators, and competitor context.
- Review content should be useful on its own, not just a wrapper for affiliate links.

**Implementation impact**
- Avoid thin, generic, or purely aggregated copy.
- Content generation pipelines should require:
  - “who it is for”
  - “why it made the list”
  - strengths / weaknesses
  - comparison context
  - evidence or source-backed claims

---

### 7) Google: Product structured data
**URL:** https://developers.google.com/search/docs/appearance/structured-data/product

**Why keep it in the project**
- Important for deciding markup on editorial comparison pages versus purchase pages.

**What to learn**
- Google distinguishes between:
  - Product snippets for non-purchase/editorial product pages
  - Merchant listings for pages where users can buy directly from you
- Product snippets can include review-related information and editorial pros/cons.

**Implementation impact**
- Heyup Newsroom and editorial comparison pages may use Product snippet-oriented markup where eligible.
- Store/product pages should be evaluated separately for Merchant listing support.
- Product variant modeling matters if multiple variants are presented.

---

### 8) Google: Review snippet structured data
**URL:** https://developers.google.com/search/docs/appearance/structured-data/review-snippet

**Why keep it in the project**
- Relevant if Heyup wants star/rating-related rich results where eligible.

**What to learn**
- Review snippets can show ratings and summary information in rich results.
- Markup eligibility depends on valid structured data and content context.

**Implementation impact**
- Do not assume every article qualifies.
- Schema should be tied to actual visible page content and valid page types.

---

### 9) Google: Qualify outbound links
**URL:** https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links

**Why keep it in the project**
- Directly relevant to affiliate-link implementation.

**What to learn**
- Google recommends `rel="sponsored"` for ads or paid placements.
- `nofollow` remains acceptable, but `sponsored` is preferred for paid links.

**Implementation impact**
- Affiliate link components should support `rel="sponsored"` by default.
- QA should verify outbound link attributes across templates.

---

## Recommended upload order into ChatGPT Project

1. This markdown pack
2. The CSV tracking file
3. Later: Heyup internal docs, taxonomy, schemas, QA checklists, template specs

---

## Suggested follow-up internal docs

- 00_project_brief.md
- 01_success_metrics.md
- 02_affiliate_compliance_rules.md
- 03_content_taxonomy.md
- 04_page_templates.md
- 05_internal_linking_rules.md
- 06_product_data_schema.md
- 07_article_schema.md
- 08_affiliate_link_schema.md
- 09_refresh_workflows.md
- 10_analytics_events.md
- 11_editorial_qa_checklist.md
