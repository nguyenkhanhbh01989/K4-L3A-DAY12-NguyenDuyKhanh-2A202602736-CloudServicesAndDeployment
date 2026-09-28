import sys, re, json
import time
from datetime import datetime, timezone

c = open('app/config.py', encoding='utf-8').read().replace('class Settings(BaseSettings):', '''class Settings(BaseSettings):
    port: int = 8000
    agent_api_key: str
    redis_url: str = 'redis://localhost:6379/0'
    rate_limit_per_minute: int = 10
    monthly_budget_usd: float = 10.0
    log_level: str = 'INFO'
''')
open('app/config.py', 'w', encoding='utf-8').write(c)

l = open('app/logging_utils.py', encoding='utf-8').read().replace('raise NotImplementedError("TODO (CP1): cài đặt log_event")', '''print(json.dumps({'event': event, 'level': level.lower(), 'timestamp': datetime.now(timezone.utc).isoformat(), **kwargs}), flush=True)''')
open('app/logging_utils.py', 'w', encoding='utf-8').write(l)

m = open('app/main.py', encoding='utf-8').read().replace('raise NotImplementedError("TODO (CP1): cài đặt /health")', '''if lifecycle.shutting_down:
        return JSONResponse(status_code=503, content={'status': 'shutting_down'})
    return {"status": "ok", "version": "1.0.0", "service": "llm_agent"}'''
).replace('raise NotImplementedError("TODO (CP4): cài đặt /ready")', '''if lifecycle.shutting_down:
        return JSONResponse(status_code=503, content={'status': 'shutting_down'})
    if not store.ping():
        return JSONResponse(status_code=503, content={'status': 'not ready', 'redis': False})
    return {'status': 'ready', 'redis': True}'''
).replace('raise NotImplementedError("TODO (CP3/CP4): cài đặt /ask")', '''limiter.check(user_id)
    guard.check(user_id)
    history = store.get_history(user_id)
    result = ask_llm(payload.question, history)
    store.append(user_id, 'user', payload.question)
    store.append(user_id, 'assistant', result['answer'])
    guard.record(user_id, result['cost_usd'])
    log_event('ask_completed', user_id=user_id, tokens_in=result['tokens_in'], tokens_out=result['tokens_out'], cost_usd=result['cost_usd'])
    return {'answer': result['answer'], 'user_id': user_id, 'history_length': len(history), 'cost_usd': result['cost_usd'], 'tokens': {'in': result['tokens_in'], 'out': result['tokens_out']}}''')
open('app/main.py', 'w', encoding='utf-8').write(m)

a = open('app/auth.py', encoding='utf-8').read().replace('raise NotImplementedError("TODO (CP3): cài đặt verify_api_key")', '''expected_key = get_settings().agent_api_key
    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing API key")
    return x_user_id if x_user_id else ANONYMOUS_USER'''
)
open('app/auth.py', 'w', encoding='utf-8').write(a)

r = open('app/rate_limiter.py', encoding='utf-8').read().replace('raise NotImplementedError("TODO (CP3): cài đặt hit_count")', '''now = now if now is not None else time.time()
        key = self._key(user_id)
        self.client.zremrangebyscore(key, 0, now - WINDOW_SECONDS)
        return self.client.zcard(key)'''
).replace('raise NotImplementedError("TODO (CP3): cài đặt check")', '''now = now if now is not None else time.time()
        key = self._key(user_id)
        if self.hit_count(user_id, now) >= self.limit:
            raise HTTPException(status_code=429, detail="rate limit exceeded", headers={"Retry-After": str(WINDOW_SECONDS)})
        self.client.zadd(key, {f"{now}:{uuid.uuid4().hex}": now})
        self.client.expire(key, WINDOW_SECONDS)'''
)
open('app/rate_limiter.py', 'w', encoding='utf-8').write(r)

cg = open('app/cost_guard.py', encoding='utf-8').read().replace('raise NotImplementedError("TODO (CP3): cài đặt spent")', '''val = self.client.get(self._key(user_id, month))
        return float(val) if val is not None else 0.0'''
).replace('raise NotImplementedError("TODO (CP3): cài đặt check")', '''if self.spent(user_id, month) + estimated_cost > self.budget:
            raise HTTPException(status_code=402, detail="monthly budget exceeded")'''
).replace('raise NotImplementedError("TODO (CP3): cài đặt record")', '''key = self._key(user_id, month)
        total = self.client.incrbyfloat(key, cost)
        self.client.expire(key, KEY_TTL_SECONDS)
        return float(total)'''
)
open('app/cost_guard.py', 'w', encoding='utf-8').write(cg)

st = open('app/store.py', encoding='utf-8').read().replace('raise NotImplementedError("TODO (CP4): cài đặt ping")', '''try:
            return self.client.ping()
        except Exception:
            return False'''
).replace('raise NotImplementedError("TODO (CP4): cài đặt append")', '''key = self._key(user_id)
        self.client.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))
        self.client.ltrim(key, -HISTORY_MAX_MESSAGES, -1)
        self.client.expire(key, HISTORY_TTL_SECONDS)'''
).replace('raise NotImplementedError("TODO (CP4): cài đặt get_history")', '''key = self._key(user_id)
        raw = self.client.lrange(key, 0, -1)
        return [json.loads(x) for x in raw] if raw else []'''
)
open('app/store.py', 'w', encoding='utf-8').write(st)

lc = open('app/lifecycle.py', encoding='utf-8').read().replace('raise NotImplementedError("TODO (CP4): cài đặt request_shutdown")', '''self.shutting_down = True
        previous = self._previous.get(signum)
        if callable(previous):
            previous(signum, frame)'''
).replace('raise NotImplementedError("TODO (CP4): cài đặt install")', '''for sig in (signal.SIGTERM, signal.SIGINT):
            self._previous[sig] = signal.getsignal(sig)
            signal.signal(sig, self.request_shutdown)'''
)
open('app/lifecycle.py', 'w', encoding='utf-8').write(lc)
