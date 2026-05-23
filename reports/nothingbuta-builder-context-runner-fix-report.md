# NothingButA Builder Context Runner Fix Report

Generated: 2026-05-20T12:35:01-04:00

## Status

PASS

## Fixed

The builder-context runner now adds the dashboard folder to Python sys.path before importing:

app.nothingbuta_research_guidance

## Why This Was Needed

The temporary Python runner lives in the Windows temp directory, so Python could not see the local dashboard/app package by default.

## Runner

C:\Users\dmchris\OpenClawOps\scripts\nova-nothingbuta-builder-context.ps1