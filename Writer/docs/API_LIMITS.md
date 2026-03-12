# API Rate Limits — DeepSeek

Official DeepSeek API documentation explicitly states that the DeepSeek API does not impose per-user rate limits. This document captures what is documented, what is not specified, and practical recommendations for how to configure a client-side rate limiter when integrating with the DeepSeek API.

1) Official rate-limit stance
- DeepSeek API does not constrain a user’s rate limit. In practice, this means there are no published RPM (requests per minute) or TPM (tokens per minute) quotas advertised for individual accounts. Source: https://api-docs.deepseek.com/quick_start/rate_limit

2) Practical behavior under load
- If the DeepSeek servers are under high traffic pressure, responses may be delayed. The connection may stay open, and you may observe special line formats during streaming vs non-streaming requests:
  - Non-streaming requests: the server may emit empty lines while the response is being produced.
  - Streaming requests: keep-alive comments (": keep-alive" in SSE) may be sent to keep the connection alive.
- These formats do not affect JSON payload parsing by the SDK, but your client should be prepared to handle empty lines or keep-alive tokens as part of the streaming/non-streaming behavior.
- If inference has not started within 10 minutes, the server will close the connection.

3) Model types and tiered limits
- The official rate-limit page does not publish tier-based or per-model limits (e.g., separate limits for deepseek-chat vs deepseek-coder). Labeling and model variants exist (e.g., chat vs reasoning modes), but no published per-model rate quotas are documented.

4) What this means for your rate limiter configuration
- There are no published server-enforced RPM/TPM values to hard-code in a rate limiter. Do not rely on an externally enforced numeric limit from DeepSeek when configuring client-side throttling.
- You should implement your own rate control and retry strategy to balance throughput with stability and user experience. The repository currently uses a 3-attempt retry policy with exponential backoff, which is a reasonable baseline when network or server delays occur.
- Recommended client-side practices:
  * Use a general-purpose rate limiter (e.g., token-bucket or leaky-bucket) to cap in-flight requests and control concurrency.
  * Respect server hints and streaming behavior: handle empty-line chunks gracefully for non-streaming responses and preserve SSE keep-alive handling for streaming responses.
  * Implement retries with exponential backoff on timeouts or transient errors. The current implementation uses 3 retries; consider increasing or adapting this based on observed latency and success rate in your environment.
  * If you observe persistent delays during high load, throttle further and/or switch to a backoff strategy before retrying.

5) Model differences
- The official docs do not publish separate rate limits for different models (e.g., deepseek-chat vs deepseek-reasoner). Plan your rate control based on your application requirements rather than any model-specific quotas published by the provider.

6) Sources
- Rate Limit page (official): https://api-docs.deepseek.com/quick_start/rate_limit
- General docs hub (context for APIs): https://platform.deepseek.com/docs

## Recommendations for production configuration
- Implement a client-side rate limiter to cap concurrency and regulate request throughput according to your service level goals.
- Use exponential backoff for retries (current baseline: 3 retries).
- Prepare for streaming vs non-streaming variations by robustly handling empty-lines and keep-alive signals.
- Monitor latency and error rates; adjust your rate limiter thresholds to maintain stable throughput without overwhelming the API.

Note: This document is based on the official rate-limit documentation. If DeepSeek publishes new RPM/TPM limits or tiered-per-model quotas, update this page with the exact numbers and preserve citations.

Source citations:
- https://api-docs.deepseek.com/quick_start/rate_limit
- https://platform.deepseek.com/docs
