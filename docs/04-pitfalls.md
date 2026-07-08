# Pitfalls And How To Design Around Them

## Discovery is supposed to be noisy — validation is the filter, not a sign of a bad query

A broad discovery pass (phase 2) will always include some companies that do not actually match the
criterion — pulled in from generic "top funded startups" lists, adjacent categories, or weak keyword
overlap. This is expected. Do not hand-filter the pool before validation on the assumption that
weaker-looking entries are wrong; some of them will confirm. Phase 3 exists specifically to separate
real matches from lookalikes — that is its job, not a symptom of phase 2 doing something wrong.

## Structured schema strictness controls list size more than query wording does

If a discovery call's schema marks fields like `evidence` or `source_url` as required on every array
item, the model will silently drop any company it found but could not cleanly cite — shrinking the
result list without any error being raised. For a broad discovery call, require only `company_name`.
Add stricter requirements at the validation phase, where a result without a clear status is not useful
regardless.

## A blended search call can starve one facet in favor of another

A single `standard` search call that asks for several independent facets (community discussion,
comparison pages, directories, funding news) in one request can let whichever facet has the most raw
web content dominate the results, leaving a facet like funding/expansion news underrepresented — not
because the signal does not exist, but because "best of" list content is simply more abundant online.
If one facet is producing too few results, split it into its own dedicated call.

## Community sources answer "does this pattern exist," not "which company has it"

Forums and community threads are strong evidence that a pattern is real and discussed — a poster
describing their own company's exact situation is compelling — but posters are almost always anonymous.
Treat these as validation that the underlying pattern exists in the wild, and rely on funding news,
expansion announcements, and hiring posts for company names you can actually act on.

## A common company name is a real risk at scale

Company names collide. A validation call asked to check "Plum" can return solid-looking evidence about
an unrelated company that also happens to be named Plum, if that company has a stronger web presence
than the actual target. The same risk applies to any short, generic, or widely-reused name.

Before accepting a "confirmed" verdict, check that the evidence's industry, country, and approximate
size are consistent with the context that first surfaced the company in phase 2 — its original source
URL and the search facet it came from. If a company was discovered via a UK fintech job posting and the
validation evidence describes a skincare brand, that is a name collision, not a match, regardless of
what status the model assigned.

## Criterion confirmation and firmographic fit are two separate questions

A validation call can correctly confirm that a company operates the qualitative trait and still be a
poor fit — because the company is far larger than the target firmographic band, or because it is a
national subsidiary of a much larger multinational rather than an independent buyer. Always cross-check
confirmed candidates against the firmographic band as a separate step (phase 5), and exclude anything
outside it even when the qualitative criterion genuinely held up.

## A single validation pass can still be wrong for small or ambiguous companies

Companies with a thin web footprint are the ones most likely to produce an unreliable first-pass
verdict — a scrape can surface a same-named or loosely related entity without enough context to
distinguish it from the real target. Route anything with ambiguous entity identity to background
verification (phase 4) even if the first pass already labeled it "confirmed," and let the deeper,
multi-source investigation (official filings, funding press, professional network profiles) make the
final call.

## Pricing and product pages are often gated

Some of the strongest evidence for a qualitative criterion lives behind "contact sales," a login wall,
or a product tour that requires a demo request. When a validation call cannot find public evidence
either way, mark the result `unclear` and route it to background verification instead of guessing.

## Background research is asynchronous — use that

Each background verification job can take several minutes. Submitting all of them in parallel and
polling as a batch, rather than running them one at a time, is the difference between a background
phase that takes as long as its slowest job and one that takes as long as the sum of all of them.

## A vague criterion produces a vague search

"Flexible pricing," "good company culture," or "cares about sustainability" are not checkable
statements — a search built around them will not know what evidence would satisfy it. Rewrite every
qualitative criterion as a concrete, checkable statement before running phase 2: "offers a self-serve
pay-as-you-go plan without a sales call," not "flexible pricing."
