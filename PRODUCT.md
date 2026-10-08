# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Sellers of cash-on-delivery (COD) goods in Tunisia, usually running a small shop through Instagram, Facebook or WhatsApp. The same person works on a phone (quick decisions between other tasks) and on a laptop (volume), interchangeably, sometimes with an assistant. Customers write orders in Tunisian Darija (Arabic script or Arabizi), French or a mix, often with an address like "near the mosque".

Confirmed with the owner: phone and desk are used interchangeably. The interface language is English for now, with Arabic (RTL) and French expected later.

## Product Purpose

Wasel scores the refusal risk of a COD order placed in chat (0 to 100) and helps the seller resolve the risky ones before a courier is sent. It explains each score with the customer's own words, drafts the one question that would reduce the risk (confirm, complete the address, or pay first), and rescores when the customer replies, showing what changed. A refused parcel costs the seller a wasted trip, so success is fewer refused deliveries.

## Positioning

The score is explained with quotes from the customer's own message, and the reasons are shown as a diff when the customer answers (v1 87 to v2 16). The LLM extracts facts and code verifies every quote; the score is computed in code, never by the LLM. A person sends the drafts. A neighbouring address-validation or fraud tool does not read the conversation and does not show its reasoning in the customer's words.

## Constraints and facts to preserve

- All data in the repository and the demo is synthetic. Wasel is a prototype, not a validated risk model; the interface must not imply otherwise.
- Risk tier is never carried by colour alone (shape plus label plus number).
- The product reads Arabic-script and Latin-script text side by side; customer text uses `dir="auto"`.
- Accessibility: WCAG AA contrast, 44px touch targets, visible keyboard focus.

## Brand commitments

Name: Wasel (Arabic واصل, "arrived, connected"). Confirmed by the owner: nothing else about the current brand (logo, colours, look) is fixed, and even the name is open to discussion if a better world needs it.

## Open decisions

- Final logo and visual world (in progress).
- Interface language beyond English.
