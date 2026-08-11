# Shopify Product Content Generation Spec

Status: draft
Owner: Russell
Last Updated: 2026-03-07
Scope: current state
Source of Truth: uploaded Dify workflow YAML

## 1. Purpose
This document defines the current content-generation spec used in the Dify workflow for creating Shopify-ready product content.

## 2. Core Generation Principle
The workflow prompt enforces a strict fact-based rule:
all generated content must be derived directly from the parsed product description.
The prompt explicitly forbids invention, assumption, exaggeration, or unsupported claims.

## 3. Required Generated Fields
The workflow requires the LLM to generate the following fields:

- `name`
- `es_name`
- `overview`
- `es_overview`
- `seo_description`
- `es_seo_description`
- `description`
- `es_description`
- `details`
- `es_details`

## 4. Field-Level Requirements

### Product Title
- Field: `name`
- Rule: keep the original product name, with only minor edits for clarity and impact

### Short Description
- Field: `description`
- Rule: 4 to 6 clear selling points
- Purpose: highlight key features and benefits
- Constraint: include important technical specifications where available
- Length limit: total under 400 characters

### Detailed Introduction
- Field: `details`
- Rule: 5 persuasive reasons to buy
- Constraint: each reason must expand on a real selling point backed by the source specs

### Overview
- Field: `overview`
- Rule: very short product summary
- Length limit: maximum 20 English words

### SEO Description
- Field: `seo_description`
- Rule: concise informational meta description
- Length limit: maximum 20 English words

### Translation
- Every primary field must also have a Spanish equivalent in `es_*` fields

## 5. Required Output Shape
The LLM is expected to return a strict JSON object containing:
- English fields
- Spanish fields
- structured description arrays
- structured details objects with `reason1` to `reason5`

## 6. Post-Processing Rules
After generation, the workflow:
- parses the JSON response
- concatenates `description` bullets into a short description block
- formats `details` into HTML sections
- converts the 5 reasons into a display block titled:
  `5 Reasons to try [Product]`
- creates a Spanish equivalent block:
  `5 Razones para probar [Product]`

## 7. Effective Content Model
In practice, the workflow turns a source product page into the following content layers:
- concise title
- short feature summary
- overview snippet
- SEO meta description
- persuasive long-form “5 reasons” copy
- translated equivalents

## 8. Strengths of Current Spec
- strongly constrained against hallucinated product claims
- structured enough for automation
- reusable for Shopify product creation
- useful for SEO and collection display
- translation-ready

## 9. Current Limitations
- optimized for product listings, not newsroom/editorial articles
- limited to one translation target in the current workflow
- fixed structure may not fit all product categories
- no explicit scoring or confidence field
- no citation or evidence trace is preserved from the source page

## 10. Suggested Future Improvements
- add source-trace fields for specs and claims
- add category-aware templates for different device types
- distinguish between consumer copy and editorial copy
- support more languages
- add quality checks for duplicate or overly generic phrasing
- add structured spec extraction alongside marketing copy

## 11. Relevance to MVP Knowledge Base
This spec is useful for:
- `20_cms_and_seo_capabilities.md`
- `21_content_taxonomy_and_page_types.md`
- `40_technical_systems_and_integrations.md`

It should be treated as the current standard for automated Shopify product-listing copy, not as a universal content standard for all Heyup content.
