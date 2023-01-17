import json
import sys
import time
import os
import subprocess

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} config ffmpeg", file=sys.stderr)
        sys.exit(1)

    s = json.load(open(sys.argv[1]))
    tmp_args = f"""tsp --receive-timeout 10000 -I dvb --signal-timeout 10 --guard-interval auto --bandwidth {s["bandwidth"]} --adapter {s["adapter"]} --delivery-system {s["system"]} --frequency {s["frequency"]*int(1e6)} --transmission-mode auto --spectral-inversion off"""
    prgs = json.loads(subprocess.check_output(f'''{tmp_args} -O fork "ffprobe -print_format json -show_error -show_programs -loglevel quiet -"''', shell=True))
    #print(prgs)
    
    for p in prgs["programs"]:
        if p["program_id"] in s["reserved_pids"]: continue
        print(f'{p["program_id"]} = {p["tags"]["service_name"] if "tags" in p else "N/A"}')
        tmp_args += f''' -P fork "tsp -P zap {p["program_id"]} | {sys.argv[2]} -copyts -flags +output_corrupt -i - -map 0:v:0? -map 0:a:0? -metadata \'title={p["tags"]["service_name"] if "tags" in p else "N/A"}\' -vcodec copy -copyinkf -acodec aac -aac_coder twoloop{" -af '"+s["filters"][str(p["program_id"])]["audio_filters"]+"'" if str(p["program_id"]) in s["filters"] else ""} -b:a 256k -loglevel quiet -f flv {s["pub_url"]}{p["program_id"]}"'''
    tmp_args += " -O drop"

    print(f"start streaming from tuner {s['adapter']}")

    #print(tmp_args)
    while True:
       os.system(tmp_args)
       print(f"restart mux {s['frequency']}", file=sys.stderr)
       time.sleep(5)
