from __future__ import annotations

import html
import logging
from pathlib import Path

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

try:
    from .nothingbuta_state import load_candidates, project_root, run_local_review, update_candidate
except ImportError:
    from nothingbuta_state import load_candidates, project_root, run_local_review, update_candidate

logger = logging.getLogger("nova.nothingbuta_routes")

router = APIRouter()


@router.get("/api/nothingbuta/queue")
def nothingbuta_queue() -> JSONResponse:
    """Return local-only NothingButA review candidates."""
    try:
        return JSONResponse(load_candidates())
    except Exception as exc:
        logger.exception("NothingButA queue API failed.")
        return JSONResponse({"error": str(exc)}, status_code=500)


@router.get("/nothingbuta/preview/{candidate_id}/", response_class=HTMLResponse)
def nothingbuta_preview(candidate_id: str) -> HTMLResponse:
    """Serve a local-only preview from disk."""
    try:
        for candidate in load_candidates():
            if candidate.get("candidate_id") != candidate_id:
                continue

            preview_rel = candidate.get("local_preview_path") or ""
            preview_path = project_root() / preview_rel

            if not preview_path.exists():
                return HTMLResponse(
                    f"<h1>Preview missing</h1><pre>{html.escape(str(preview_path))}</pre>",
                    status_code=404,
                )

            return HTMLResponse(preview_path.read_text(encoding="utf-8", errors="replace"))

        return HTMLResponse("<h1>Candidate not found</h1>", status_code=404)
    except Exception as exc:
        logger.exception("NothingButA preview failed.")
        return HTMLResponse(f"<h1>Preview failed</h1><pre>{html.escape(str(exc))}</pre>", status_code=500)


@router.post("/nothingbuta/review")
def nothingbuta_review(candidate_id: str = Form(...)) -> RedirectResponse:
    """Run local Big Brother review and return to dashboard."""
    try:
        run_local_review(candidate_id)
    except Exception:
        logger.exception("NothingButA review action failed.")

    return RedirectResponse(url="/nothingbuta", status_code=303)


@router.post("/nothingbuta/approve")
def nothingbuta_approve(candidate_id: str = Form(...)) -> RedirectResponse:
    """Approve candidate for staging only; does not publish."""
    try:
        update_candidate(candidate_id, "approve")
    except Exception:
        logger.exception("NothingButA approve action failed.")

    return RedirectResponse(url="/nothingbuta", status_code=303)


@router.post("/nothingbuta/regenerate")
def nothingbuta_regenerate(
    candidate_id: str = Form(...),
    notes: str = Form(...),
) -> RedirectResponse:
    """Request regeneration with Chris notes."""
    try:
        update_candidate(candidate_id, "regenerate", notes)
    except Exception:
        logger.exception("NothingButA regenerate action failed.")

    return RedirectResponse(url="/nothingbuta", status_code=303)


@router.post("/nothingbuta/delete")
def nothingbuta_delete(
    candidate_id: str = Form(...),
    notes: str = Form(""),
) -> RedirectResponse:
    """Archive candidate locally so Nova can learn."""
    try:
        update_candidate(candidate_id, "delete", notes)
    except Exception:
        logger.exception("NothingButA delete action failed.")

    return RedirectResponse(url="/nothingbuta", status_code=303)

# === NOTHINGBUTA_DEDICATED_PAGE_ROUTE START ===
@router.get("/nothingbuta", response_class=HTMLResponse)
def nothingbuta_page() -> HTMLResponse:
    """
    Dedicated local-only review page for NothingButA candidates.

    This stays on the existing port 8788 dashboard site.
    It does not publish, buy domains, add ads, add affiliate links, or push code.
    """
    try:
        page = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NothingButA Sites | Nova Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: #0f172a;
      color: #e5e7eb;
    }

    header {
      padding: 22px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.35);
      background: #111827;
    }

    main {
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px;
    }

    a {
      color: #93c5fd;
    }

    .topbar {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
    }

    .back-link {
      display: inline-block;
      padding: 10px 14px;
      border-radius: 12px;
      background: #1f2937;
      color: #e5e7eb;
      text-decoration: none;
      font-weight: 700;
    }

    .card {
      margin-top: 18px;
      padding: 18px;
      border: 1px solid rgba(148, 163, 184, 0.35);
      border-radius: 18px;
      background: #111827;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.18);
    }

    .card-top,
    .actions,
    .meta {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
    }

    .score {
      min-width: 96px;
      text-align: center;
      padding: 12px;
      border-radius: 14px;
      background: #020617;
      border: 1px solid rgba(148, 163, 184, 0.35);
    }

    .score strong {
      display: block;
      font-size: 28px;
    }

    .meta span {
      padding: 5px 10px;
      border-radius: 999px;
      background: #1f2937;
      font-size: 13px;
    }

    button {
      border: 0;
      border-radius: 12px;
      padding: 10px 14px;
      font-weight: 700;
      cursor: pointer;
      background: #86efac;
      color: #052e16;
    }

    textarea {
      width: 100%;
      min-height: 84px;
      box-sizing: border-box;
      margin-top: 8px;
      border-radius: 12px;
      padding: 10px;
      border: 1px solid #334155;
    }

    form {
      margin: 0;
    }

    .form-block {
      margin-top: 14px;
    }

    details {
      margin-top: 14px;
      padding: 12px;
      border-radius: 12px;
      background: #020617;
    }

    .danger button {
      background: #fca5a5;
      color: #450a0a;
    }

    .warn button {
      background: #fde68a;
      color: #422006;
    }

    .muted {
      color: #94a3b8;
    }

    .error {
      color: #fca5a5;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>NothingButA Sites</h1>
        <p class="muted">Local-only website/tool ideas. Approval moves a candidate to staging review only. It does not publish.</p>
      </div>
      <a class="back-link" href="/">Ã¢â€ Â Back to Nova Dashboard</a>
    </div>
  </header>

  <main>
    <section class="card">
      <h2>Research Guidance Applied</h2>
      <p class="muted">These are the safe inspiration patterns Nova used before Big Brother review. No copied posts, comments, layouts, competitor text, or competitor code.</p>
      <div id="nothingbuta-guidance">Loading research guidance...</div>
    </section>

    <div id="nothingbuta-queue">Loading NothingButA candidates...</div>
  </main>

  <script>

    async function loadNothingButAGuidance() {
      const mount = document.getElementById("nothingbuta-guidance");

      if (!mount) {
        return;
      }

      try {
        const response = await fetch("/api/nothingbuta/builder-context", { cache: "no-store" });

        if (!response.ok) {
          mount.innerHTML = `<p class="error">Builder context API failed: ${response.status}</p>`;
          return;
        }

        const context = await response.json();

        const sections = [
          ["Pain points Nova is designing for", context.pain_points_to_address || []],
          ["Mobile UX patterns", context.mobile_ux_patterns || []],
          ["Result explanation patterns", context.result_explanation_patterns || []],
          ["FAQ candidates", context.faq_candidates || []],
          ["Trust and disclaimer patterns", context.trust_and_disclaimer_patterns || []],
          ["Do-not-copy rules", context.do_not_copy_notes || []]
        ];

        const cards = sections.map(([title, items]) => {
          const listItems = Array.isArray(items) && items.length
            ? items.slice(0, 5).map((item) => `<li>${escapeHtml(item)}</li>`).join("")
            : "<li>No guidance recorded yet.</li>";

          return `
            <article class="card" style="margin-top: 12px; box-shadow: none;">
              <h3>${escapeHtml(title)}</h3>
              <ul>${listItems}</ul>
            </article>
          `;
        }).join("");

        mount.innerHTML = `
          <div class="meta">
            <span>Context: ${escapeHtml(context.status || "unknown")}</span>
            <span>Research: ${escapeHtml(context.research_status || "unknown")}</span>
            <span>Mobile-first: ${context.mobile_first_required ? "yes" : "no"}</span>
            <span>No-copy: ${context.no_copy_required ? "yes" : "no"}</span>
            <span>Public clean: ${context.public_cleanliness_required ? "yes" : "no"}</span>
          </div>
          ${cards}
        `;
      } catch (error) {
        mount.innerHTML = `<p class="error">Failed to load guidance: ${escapeHtml(String(error))}</p>`;
      }
    }

    async function loadNothingButAQueue() {
      const mount = document.getElementById("nothingbuta-queue");

      try {
        const response = await fetch("/api/nothingbuta/queue", { cache: "no-store" });

        if (!response.ok) {
          mount.innerHTML = `<p class="error">Queue API failed: ${response.status}</p>`;
          return;
        }

        const candidates = await response.json();

        if (!Array.isArray(candidates) || candidates.length === 0) {
          mount.innerHTML = "<p>No NothingButA candidates are queued yet.</p>";
          return;
        }

        mount.innerHTML = candidates.map((candidate) => {
          const review = candidate.big_brother_review || {};
          const recommendations = Array.isArray(review.recommendations) && review.recommendations.length
            ? review.recommendations.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
            : "<li>No review recommendations yet.</li>";

          return `
            <article class="card">
              <div class="card-top">
                <div>
                  <h2>${escapeHtml(candidate.site_name || "Untitled candidate")}</h2>
                  <p>${escapeHtml(candidate.primary_user_problem || "")}</p>
                </div>
                <div class="score">
                  <strong>${escapeHtml(String(review.overall_score ?? "Ã¢â‚¬â€"))}</strong>
                  <span>Review</span>
                </div>
              </div>

              <div class="meta">
                <span>State: ${escapeHtml(candidate.state || "unknown")}</span>
                <span>Decision: ${escapeHtml(candidate.chris_decision || "pending")}</span>
                <span>SEO: ${escapeHtml(String(candidate.seo_score ?? 0))}</span>
                <span>Code: ${escapeHtml(String(candidate.code_score ?? 0))}</span>
                <span>Mobile: ${escapeHtml(String(candidate.mobile_score ?? 0))}</span>
                <span>Trust: ${escapeHtml(String(candidate.trust_score ?? 0))}</span>
              </div>

              <p>
                <a href="${escapeAttribute(candidate.local_preview_url || "#")}" target="_blank" rel="noopener">
                  Open local preview
                </a>
              </p>

              <details>
                <summary>Big Brother recommendations</summary>
                <ul>${recommendations}</ul>
              </details>

              <div class="actions" style="margin-top: 14px;">
                <form method="post" action="/nothingbuta/review">
                  <input type="hidden" name="candidate_id" value="${escapeAttribute(candidate.candidate_id || "")}">
                  <button type="submit">Run Big Brother Review</button>
                </form>

                <form method="post" action="/nothingbuta/approve">
                  <input type="hidden" name="candidate_id" value="${escapeAttribute(candidate.candidate_id || "")}">
                  <button type="submit">Approve for Staging</button>
                </form>
              </div>

              <form class="form-block warn" method="post" action="/nothingbuta/regenerate">
                <input type="hidden" name="candidate_id" value="${escapeAttribute(candidate.candidate_id || "")}">
                <textarea name="notes" required placeholder="What needs to be fixed before Nova regenerates this?"></textarea>
                <button type="submit">Regenerate with Notes</button>
              </form>

              <form class="form-block danger" method="post" action="/nothingbuta/delete">
                <input type="hidden" name="candidate_id" value="${escapeAttribute(candidate.candidate_id || "")}">
                <textarea name="notes" placeholder="Optional delete/archive reason."></textarea>
                <button type="submit">Delete / Archive</button>
              </form>
            </article>
          `;
        }).join("");
      } catch (error) {
        mount.innerHTML = `<p class="error">Failed to load queue: ${escapeHtml(String(error))}</p>`;
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function escapeAttribute(value) {
      return escapeHtml(value);
    }

    async function runNothingButAAutoReview() {
      try {
        await fetch("/api/nothingbuta/auto-review", {
          method: "POST",
          cache: "no-store"
        });
      } catch (error) {
        console.warn("NothingButA auto-review failed", error);
      }
    }
    document.addEventListener("DOMContentLoaded", async () => {
      await runNothingButAAutoReview();
      await loadNothingButAGuidance();
      await loadNothingButAQueue();
    });
  </script>
</body>
</html>"""
        return HTMLResponse(page)
    except Exception as exc:
        logger.exception("NothingButA dedicated page failed.")
        return HTMLResponse(f"<h1>NothingButA page failed</h1><pre>{html.escape(str(exc))}</pre>", status_code=500)
# === NOTHINGBUTA_DEDICATED_PAGE_ROUTE END ===



# === NOTHINGBUTA_AUTO_REVIEW_ROUTE START ===
@router.post("/api/nothingbuta/auto-review")
def nothingbuta_auto_review() -> JSONResponse:
    """
    Run Big Brother review plus Little Brother auto-regeneration.

    Local-only. No publishing, domains, ads, affiliate links, lead capture, commits, or pushes.
    """
    try:
        try:
            from .nothingbuta_research_guidance import apply_builder_context_to_queue
            from .nothingbuta_auto_loop import run_auto_quality_loop
        except ImportError:
            from nothingbuta_research_guidance import apply_builder_context_to_queue
            from nothingbuta_auto_loop import run_auto_quality_loop

        guidance_result = apply_builder_context_to_queue()
        loop_result = run_auto_quality_loop()

        return JSONResponse({
            "status": "complete",
            "guidance": guidance_result,
            "quality_loop": loop_result
        })
    except Exception as exc:
        logger.exception("NothingButA auto-quality loop failed.")
        return JSONResponse({"status": "failed", "error": str(exc)}, status_code=500)
# === NOTHINGBUTA_AUTO_REVIEW_ROUTE END ===

# === NOTHINGBUTA_BUILDER_CONTEXT_API START ===
@router.get("/api/nothingbuta/builder-context")
def nothingbuta_builder_context() -> JSONResponse:
    """
    Return the current safe builder context.

    This exposes only local research-pattern guidance:
    - no copied Reddit comments
    - no copied forum posts
    - no copied competitor content
    - no scraping
    - no publishing
    - no external actions
    """
    try:
        try:
            from .nothingbuta_research_guidance import build_builder_context
        except ImportError:
            from nothingbuta_research_guidance import build_builder_context

        return JSONResponse(build_builder_context())
    except Exception as exc:
        logger.exception("NothingButA builder context API failed.")
        return JSONResponse({"status": "failed", "error": str(exc)}, status_code=500)
# === NOTHINGBUTA_BUILDER_CONTEXT_API END ===

# === NOTHINGBUTA_FACTORY_REVIEW_ROUTES START ===
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

try:
    from .nothingbuta_factory_review import (
        build_review_pipeline,
        mutate_candidate,
        read_candidate_preview,
        render_review_page,
    )
except ImportError:
    from nothingbuta_factory_review import (
        build_review_pipeline,
        mutate_candidate,
        read_candidate_preview,
        render_review_page,
    )


@router.get("/api/nothingbuta/factory-review")
def nothingbuta_factory_review_api() -> JSONResponse:
    """Return the local-only NothingButA factory review pipeline."""
    try:
        return JSONResponse(build_review_pipeline())
    except Exception as exc:
        logger.exception("NothingButA factory review API failed.")
        return JSONResponse({"status": "failed", "error": str(exc)}, status_code=500)


@router.get("/nothingbuta/factory-review", response_class=HTMLResponse)
def nothingbuta_factory_review_page() -> HTMLResponse:
    """Render the local-only NothingButA factory review page."""
    try:
        return HTMLResponse(render_review_page())
    except Exception as exc:
        logger.exception("NothingButA factory review page failed.")
        return HTMLResponse(f"<h1>Factory review failed</h1><pre>{exc}</pre>", status_code=500)


@router.get("/nothingbuta/factory-preview/{slug}/", response_class=HTMLResponse)
def nothingbuta_factory_preview(slug: str) -> HTMLResponse:
    """Render a local-only candidate preview through the dashboard."""
    try:
        return HTMLResponse(read_candidate_preview(slug))
    except Exception as exc:
        logger.exception("NothingButA factory preview failed.")
        return HTMLResponse(f"<h1>Preview failed</h1><pre>{exc}</pre>", status_code=500)


@router.post("/nothingbuta/factory-review/{tool_id}/{action}")
def nothingbuta_factory_review_action(tool_id: str, action: str) -> RedirectResponse:
    """Apply a local-only review action to a factory candidate."""
    try:
        mutate_candidate(tool_id, action)
        return RedirectResponse(url="/nothingbuta/factory-review", status_code=303)
    except Exception:
        logger.exception("NothingButA factory review action failed.")
        return RedirectResponse(url="/nothingbuta/factory-review", status_code=303)
# === NOTHINGBUTA_FACTORY_REVIEW_ROUTES END ===
