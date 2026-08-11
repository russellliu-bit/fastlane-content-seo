# Dify Auto Product Crawling Workflow

Status: draft
Owner: Russell
Last Updated: 2026-03-07
Scope: current state
Source of Truth: uploaded Dify workflow YAML

## 1. Purpose
This document summarizes the current Dify workflow used to automatically crawl external product pages, generate product content, optimize SEO fields, create Shopify products, and register local translations.

## 2. Workflow Goal
The workflow is designed to:
- crawl newly launched product information
- parse product-page content
- generate product marketing content
- generate SEO metadata
- create product records in Shopify
- localize content for additional languages

The workflow description indicates that the current source support is mainly GadgetFlow, with future expansion planned.

## 3. High-Level Workflow Stages
The workflow appears to follow this sequence:

1. Crawl source pages and extract product URLs
2. Fetch product-level content from the source page
3. Parse and normalize product name and product description
4. Send normalized product data into an LLM prompt
5. Generate structured product marketing content
6. Reformat generated content into Shopify-ready fields
7. Create product metaobject content
8. Create the Shopify product
9. Update product fields such as review link and publication state
10. Register translations for product, metaobject, and metafields

## 4. Core Inputs
Observed workflow inputs and environment dependencies include:
- User agent string
- Shopify Admin GraphQL endpoint
- Shopify admin access token
- external product page URLs
- parsed product name
- parsed product description

## 5. Core Outputs
The workflow outputs a product package that includes:
- Shopify product record
- Shopify product template metaobject
- SEO title and SEO description
- structured long-form product description
- short product features summary
- overview field
- translated content in Spanish
- review button link
- publication updates
- inventory tracking updates

## 6. Data Transformation Logic
The workflow converts raw crawled product information into a structured `product_info` object containing:
- title
- es_title
- description
- es_description
- seo_description
- es_seo_description
- overview
- es_overview
- short_description
- es_short_description

The generated long description is formatted as a “5 Reasons to try [Product]” block and converted into HTML.

## 7. Shopify Write Path
The workflow writes into Shopify in multiple steps:
- create product template metaobject
- create product
- update review button link
- update inventory tracking
- update publication channels
- fetch translatable resources
- register translations for standard product fields
- register translations for metaobject fields
- register translations for metafield values

## 8. Workflow Strengths
This workflow already proves that Heyup has a functioning automation path for:
- product ingestion
- structured AI-assisted copy generation
- SEO field creation
- Shopify product creation
- multilingual content registration

## 9. Current Constraints and Risks
The YAML suggests several constraints:
- current source support is narrow and mainly GadgetFlow
- some values appear hardcoded
- some collection IDs and metaobject IDs are fixed in the workflow
- product type and tags are defaulted rather than dynamically classified
- translation currently appears focused on Spanish
- business logic is embedded directly in the workflow rather than abstracted into shared services

## 10. Implications for Knowledge Base
This workflow should be treated as an implementation snapshot of how Heyup currently automates product ingestion into Shopify.
It is especially useful for:
- CMS and SEO capability mapping
- technical systems and integrations mapping
- product content generation standards
- future Codex implementation planning

## 11. Recommended Follow-up Questions
- Is this workflow still used in production?
- Which source sites are officially supported today?
- Which values are hardcoded and should become config?
- What is the production owner of this workflow?
- What is the relationship between this workflow and the Heyup Blogs API / Fastgrowth pipeline?
