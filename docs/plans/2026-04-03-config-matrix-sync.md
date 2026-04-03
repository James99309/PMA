# Config Matrix Sync to Products Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow locked (production/discontinued) configurations to fill missing spec fields and sync changes to linked CN/SG products with one click.

**Architecture:** Method B (dynamic comparison) - no new DB columns. Compare config values vs product specs at query time to determine sync status. Frontend allows editing only missing fields in locked configs. Backend reuses existing link-product sync logic and cross_sync API.

**Tech Stack:** Flask backend, Jinja2 + Tailwind + vanilla JS frontend, PostgreSQL, cross_sync REST API for SG NAS.

---

## Task 1: Frontend - Make Missing Fields Editable in Locked Configs

Modify: `app/templates/spec_template/tw_spec_config_matrix.html:456-475`

## Task 2: Frontend - Save Locked Configs with New Values

Modify: `app/templates/spec_template/tw_spec_config_matrix.html:1982-1984, 2083-2112`

## Task 3: Backend - Accept Locked Config Value Updates + Rebuild Snapshot

Modify: `app/views/spec_template.py:2233-2333`

## Task 4: Backend - Sync Status API

Add: `GET /api/configurations/{id}/sync-status` in `app/views/spec_template.py`

## Task 5: Backend - Sync Operation API + Extract Helpers

Add: `POST /api/configurations/{id}/sync-products` in `app/views/spec_template.py`

## Task 6: Frontend - Sync Status Display + Sync Button

Modify: `app/templates/spec_template/tw_spec_config_matrix.html` column headers + JS

## Task 7: I18N Translations

Modify: `app/translations/en/LC_MESSAGES/messages.po`

## Task 8: Refactor link-product to Use Shared Helpers

Modify: `app/views/spec_template.py:1995-2065, 2109-2167`
