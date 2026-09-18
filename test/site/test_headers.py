"""site/_headers: the response headers of the Cloudflare static assets, and their copy in the test server.

The end-to-end scenario only proves the CSP if the test server sends what Cloudflare sends: these tests pin
the parser of test/site/offline.py to Cloudflare's `_headers` grammar, the headers every served path gets,
and the policy itself (same-origin only, no eval, no framing).
"""

import urllib.error
import urllib.request
from pathlib import Path

import offline
import pytest

REPO = Path(__file__).resolve().parents[2]
SITE = REPO / "site"
RULES = offline.parse_headers_file(SITE / "_headers")

SECURITY = {
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
    "cross-origin-opener-policy",
    "cross-origin-resource-policy",
    "strict-transport-security",
}


def served_paths():
    """Every URL path the Worker serves: `/` and each file of site/ but the _headers file itself."""
    files = sorted(p.relative_to(SITE).as_posix() for p in SITE.rglob("*") if p.is_file())
    return ["/"] + ["/" + rel for rel in files if rel != "_headers"]


def csp_directives(value):
    return {part.split()[0]: part.split()[1:] for part in (p.strip() for p in value.split(";")) if part}


def test_every_served_path_gets_the_security_headers_and_one_cache_policy():
    no_cache = {"/", "/index.html", "/app.js", "/styles.css"}
    for path in served_paths():
        headers = offline.headers_for(RULES, path)
        assert SECURITY <= set(headers), path
        expected = "no-cache" if path in no_cache else "public, max-age=86400"
        assert path in no_cache or path.startswith("/vendor/"), path
        assert headers["cache-control"] == expected, path


def test_no_header_is_set_by_two_rules_for_the_same_path():
    # Cloudflare joins repeated headers with ", ": two Cache-Control rules would combine into one value.
    for path in served_paths():
        names = [name for pattern, headers, _ in RULES if offline.rule_matches(pattern, path) for name in headers]
        assert len(names) == len(set(names)), (path, names)


def test_the_policy_allows_the_site_origin_only():
    csp = csp_directives(offline.headers_for(RULES, "/")["content-security-policy"])
    assert csp == {
        "default-src": ["'none'"],
        "script-src": ["'self'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "connect-src": ["'self'"],
        "base-uri": ["'none'"],
        "form-action": ["'none'"],
        "frame-ancestors": ["'none'"],
    }


def test_parser_follows_the_cloudflare_grammar(tmp_path):
    path = tmp_path / "_headers"
    path.write_text(
        "# comment\n/*\n  X-A: 1\n  X-B: b: c\n  x-a: 2\n\n/static/*\n  ! X-A\n  X-C: 3\n/exact\n  X-D: 4\n",
        encoding="utf-8",
    )
    rules = offline.parse_headers_file(path)
    assert rules == [
        ("/*", {"x-a": "1, 2", "x-b": "b: c"}, []),
        ("/static/*", {"x-c": "3"}, ["x-a"]),
        ("/exact", {"x-d": "4"}, []),
    ]
    assert offline.headers_for(rules, "/") == {"x-a": "1, 2", "x-b": "b: c"}
    assert offline.headers_for(rules, "/static/app.js") == {"x-b": "b: c", "x-c": "3"}
    assert offline.headers_for(rules, "/exact") == {"x-a": "1, 2", "x-b": "b: c", "x-d": "4"}
    assert offline.headers_for(rules, "/exact/more") == {"x-a": "1, 2", "x-b": "b: c"}


@pytest.mark.parametrize(
    "text",
    [
        "  X-A: 1\n",  # header before any path
        "/*\n  not a header\n",  # neither `Name: value` nor `! Name`
        "/*\n  X-A:\n",  # no value
        "/*\n  X A: 1\n",  # space in the name
        "/*\n/a\n  X-A: 1\n",  # a rule without header
        "/a/:id\n  X-A: 1\n",  # placeholder: not supported by the test server
        "/*/*\n  X-A: 1\n",  # two splats: refused by Cloudflare
        "/*\n  X-A: " + "a" * 2000 + "\n",  # longer than Cloudflare's line limit
    ],
)
def test_parser_refuses_what_cloudflare_would_skip(tmp_path, text):
    path = tmp_path / "_headers"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        offline.parse_headers_file(path)


def fetch(url):
    try:
        with urllib.request.urlopen(url) as response:
            return response.status, response.headers
    except urllib.error.HTTPError as error:
        return error.code, error.headers


def test_the_test_server_sends_the_production_headers():
    base, server = offline.serve(SITE)
    try:
        status, headers = fetch(base)
        assert status == 200
        for name, value in offline.headers_for(RULES, "/").items():
            assert headers[name] == value, name
        status, headers = fetch(base + "vendor/mdi/mdi.js")
        assert status == 200 and headers["cache-control"] == "public, max-age=86400"
        # like Cloudflare, the configuration file is not served
        assert fetch(base + "_headers")[0] == 404
    finally:
        server.shutdown()


def test_a_folder_without_headers_file_is_served_plain(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    base, server = offline.serve(tmp_path)
    try:
        status, headers = fetch(base)
        assert status == 200 and headers["content-security-policy"] is None
    finally:
        server.shutdown()
