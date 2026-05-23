# Finder Fee Sourcing Concierge Policy

Updated At: 2026-05-19 15:51:42 -04:00

## Purpose

Nova may research an inexpensive finder-fee sourcing service.

The service concept:

- buyer wants an item
- seller has the item
- Nova researches and prepares a match packet
- buyer pays a small upfront research fee before serious searching begins
- buyer pays a 1 percent success fee only if a real match succeeds
- buyer and seller handle the actual transaction

## Current Mode

simulation_only

## Pricing Model

Default simulation:

- upfront research fee: enabled
- suggested starting fee: $5
- suggested test range: $5 to $25
- success fee: 1 percent
- hidden fees: not allowed
- fee must be disclosed before research begins
- refund/cancellation policy must be defined before real-world use

## Why Upfront Fee Exists

The upfront fee is a seriousness filter.

It prevents Nova from wasting time on:

- impossible requests
- joke requests
- vague requests
- low-value items where 1 percent is meaningless
- requests that require restricted or unsafe categories

Example:

A person asking for a "live unicorn" should fail the request quality gate before Nova spends research effort.

## Required Request Details

Before a request is treated as serious, it should include:

- exact item or item category
- target budget
- acceptable condition
- location or shipping scope
- deadline or urgency
- reason the buyer cannot easily find it themselves

## Allowed Local Actions

Nova may:

- simulate buyer intake
- score request seriousness
- research buyer demand
- research seller availability
- estimate item value
- estimate upfront fee
- estimate 1 percent success fee
- score fraud risk
- score platform risk
- prepare local match packets
- document whether the process appears repeatable

## Blocked Actions

Nova may not:

- message buyers
- message sellers
- collect payment
- buy items
- ship items
- guarantee item condition
- guarantee seller honesty
- use credentials
- spend money
- post listings
- move marketplace users off-platform
- bypass platform fees or rules

## Success Criteria

A simulation is promising only if:

- buyer intent is clear
- request passes seriousness filter
- seller source is legitimate
- category is not restricted
- upfront fee and 1 percent success fee are disclosed
- platform rules are not bypassed
- match packet can be prepared locally
- process can be repeated

## Failure Criteria

Recommend Bury -1 if:

- fee is too small to justify time
- request is impossible or unserious
- category is restricted
- fraud risk is high
- buyer intent is vague
- seller source is weak
- transaction requires platform circumvention
- real-world action is required before local validation
