// Cloudflare Worker — dashboard refresh proxy
// Stores GITHUB_PAT and REFRESH_KEY as Worker secrets (never in source)
//
// Deploy steps:
//   1. Go to https://workers.cloudflare.com → Create a Service → paste this file
//   2. Settings → Variables → add two secrets:
//        GITHUB_PAT  = your GitHub PAT (workflow scope)
//        REFRESH_KEY = any random string, e.g. "misfit2026" (embed same string in dashboard)
//   3. Copy the Worker URL (e.g. https://misfit-refresh.YOUR_NAME.workers.dev)
//   4. Paste it into GH_WORKER_URL in index.html

const GH_OWNER    = 'alireza12t';
const GH_REPO     = 'alireza12t.github.io';
const GH_WORKFLOW = 'update-running-dashboard.yml';

export default {
  async fetch(request, env) {
    // CORS — only allow requests from the dashboard origin
    const origin = request.headers.get('Origin') || '';
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Refresh-Key',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders });
    }

    // Check shared key — protects against random abuse
    const key = request.headers.get('X-Refresh-Key') || '';
    if (!env.REFRESH_KEY || key !== env.REFRESH_KEY) {
      return new Response(JSON.stringify({ error: 'Forbidden' }), {
        status: 403, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Trigger GitHub Actions workflow_dispatch
    const ghRes = await fetch(
      `https://api.github.com/repos/${GH_OWNER}/${GH_REPO}/actions/workflows/${GH_WORKFLOW}/dispatches`,
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${env.GITHUB_PAT}`,
          Accept: 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
          'User-Agent': 'misfit-dashboard',
        },
        body: JSON.stringify({ ref: 'master' }),
      }
    );

    if (ghRes.status === 204) {
      return new Response(JSON.stringify({ ok: true }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const text = await ghRes.text();
    return new Response(JSON.stringify({ error: `GitHub ${ghRes.status}`, detail: text }), {
      status: ghRes.status, headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
};
