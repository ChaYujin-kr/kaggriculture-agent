"""Download the newest public agents (up to 80 kernels) into research/ladder_pool/ for fingerprinting."""
import sys, os, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_refresh as dr

DST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "ladder_pool")
os.makedirs(DST, exist_ok=True)
refs = dr.newest_kernels(80)
print(len(refs), "kernels", flush=True)
for ref in refs:
    name = ref.split("/")[1][:40]
    if os.path.exists(os.path.join(DST, name + ".py")):
        continue
    try:
        p = dr.fetch_agent(ref)
    except Exception as e:
        print("ERR", ref, e, flush=True)
        continue
    if p:
        shutil.copy(p, os.path.join(DST, name + ".py"))
        print("OK ", ref, os.path.getsize(p) // 1024, "KB", flush=True)
    else:
        print("-- ", ref, flush=True)
