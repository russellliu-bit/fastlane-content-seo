# Shopify Product Creation and Translation Flow

Status: draft
Owner: Russell
Last Updated: 2026-03-07
Scope: current state
Source of Truth: uploaded Dify workflow YAML

## 1. Purpose
This document explains how the current Dify workflow creates Shopify products and registers translations.

## 2. Shopify Endpoint
The workflow uses the Shopify Admin GraphQL API.

## 3. Main Creation Flow
The observed write flow is:

1. Create product template metaobject
2. Create Shopify product
3. Update review button link
4. Update inventory tracking
5. Publish to all publication channels
6. Fetch translatable resources for metaobject
7. Register metaobject translations
8. Fetch translatable resources for product
9. Register product translations
10. Fetch translatable resources for product metafields
11. Register metafield translations

## 4. Metaobject Creation
The workflow first creates a `product_template` metaobject.
Observed fields include:
- `product_features`
- `product_name`

This metaobject is later linked back to the product through a custom metafield.

## 5. Product Creation
The workflow creates a Shopify product with observed fields such as:
- `title`
- `descriptionHtml`
- `productType`
- `tags`
- `status`
- `publishedAt`
- `vendor`
- `templateSuffix`
- `seo.title`
- `seo.description`
- `collectionsToJoin`
- `metafields`

## 6. Observed Product Defaults
The current workflow appears to default several values:
- product type: `Wishing`
- status: `DRAFT`
- template suffix: `product-template-wishing`
- tags: static category tags
- collection membership: fixed collection IDs
- tryout steps: fixed metaobject ID
- brands field: blank by default

These defaults suggest current automation is working, but also indicate a need for future configuration cleanup.

## 7. Observed Product Metafields
The workflow writes or updates metafields including:
- `custom.product_details`
- `custom.tryout_tag`
- `custom.review_button_link`
- `custom.tryout_steps`
- `custom.product_template`
- `custom.release_on`
- `custom.brands`

## 8. Review Link Update
After product creation, the workflow updates `custom.review_button_link` using an Okendo review URL built from the new Shopify product ID.

## 9. Inventory and Publication Updates
After creation, the workflow also:
- updates inventory tracking for the created variant
- queries available publications
- publishes the product across all publication channels

This suggests the workflow is designed to mimic the operational state of manually created products.

## 10. Translation Flow Overview
The workflow handles translation in three separate layers:

### A. Metaobject Translation
- fetch translatable content for the `product_template` metaobject
- register Spanish translations for fields such as:
  - `product_name`
  - `product_features`

### B. Product Translation
- fetch translatable content for the product itself
- register Spanish translations for:
  - `title`
  - `body_html`
  - `meta_title`
  - `meta_description`

### C. Metafield Translation
- fetch metafield IDs from the created product
- locate the `product_details` metafield
- fetch its translatable content digest
- register Spanish translation for the metafield value

## 11. Why the Translatable Resource Step Matters
The workflow relies on Shopify translatable resource digests before calling `translationsRegister`.
This means translation is not a simple field overwrite; it follows Shopify’s translation registration model.

## 12. Operational Significance
This flow proves that Heyup already has working automation for:
- product creation
- product templating
- product-level SEO fields
- post-create enrichment
- publication handling
- multilingual registration

## 13. Risks and Technical Debt
The YAML suggests likely technical debt in:
- hardcoded IDs
- limited source support
- mixed business logic and infrastructure logic in one workflow
- limited language support
- default category/tag assumptions

## 14. Recommended Follow-up Improvements
- replace hardcoded IDs with configuration or lookup logic
- separate content generation from product creation services
- add validation for category/tag/vendor assignment
- add error logging and retry visibility outside the workflow
- document all Shopify entity dependencies
- standardize translation coverage across all relevant fields

## 15. Relevance to MVP Knowledge Base
This document is directly useful for:
- `20_cms_and_seo_capabilities.md`
- `40_technical_systems_and_integrations.md`

It also provides implementation context for any Codex task involving Shopify product automation, translation, or content-template pipelines.
