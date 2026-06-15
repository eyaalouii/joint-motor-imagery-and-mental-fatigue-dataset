# ================================================
# PsychoPy Motor Imagery + Fatigue Session
# Duration: ~66 minutes | 6 blocks x 28 trials
#
# Session layout:
#   Setup             : 2 min (consent + instructions)
#   Baseline          : 5 min (2 EO + 2 EC + 1 fixation)
#   6 x MI Block      : ~6 min each (28 trials = 14L + 14R)
#   6 x Post-block    : KSS (~5s, 1 keypress) + RT (single trial) + Break (30s min, self-paced)
#   Final KSS + debrief
#
# LSL Marker scheme (complete):
#   Practice          : 5    = practice start
#   Baseline          : 1000 = EO start | 1001 = EC start
#                       1002 = fixation start | 1003 = baseline end
#   Block             : 4001-4006 = block start | 4101-4106 = block end
#   Trial             : 10 = trial start (fixation onset)
#   Cue               : 100 = left cue onset | 101 = right cue onset
#   Imagery           : 200 = left imagery start | 201 = right imagery start
#   Rest              : 300 = rest start
#   ITI               : 400 = ITI start
#   Trial end         : 11 = trial end
#   KSS               : 700 = KSS screen onset
#                       2001-2009 = rating value (e.g. 2007 = rating 7)
#   RT trial          : 30 = fixation onset | 31 = stimulus onset
#                       32 = response (hit) | 33 = miss/lapse
#   Break             : 6001-6005 = break start | 6101-6105 = break end
#   Final KSS         : 9000 = final KSS onset
#   End               : 9999 = experiment end
#
# CSV columns:
#   Block | Trial | MI_Label | KSS | Event | Marker
#   Time_lsl | Wall_time | Block_Start_lsl | Block_End_lsl
# ================================================

from psychopy import visual, core, event, gui
from pylsl import StreamInfo, StreamOutlet, local_clock
import random
import csv
import time

# ─────────────────────────────────────────
# PARTICIPANT INFO
# ─────────────────────────────────────────
win = visual.Window([1024, 768], color="black", fullscr=False)

exp_info = {
    "Participant ID": "",
    "Age": "",
    "Gender": ["Male", "Female", "Other"]
}
dlg = gui.DlgFromDict(exp_info, title="MI + Fatigue (~66 min)")
if not dlg.OK:
    core.quit()

# ─────────────────────────────────────────
# LSL SETUP
# ─────────────────────────────────────────
lsl_info = StreamInfo("MIExperiment", "Markers", 1, 0, "int32", "MI_75min")
outlet   = StreamOutlet(lsl_info)
exp_clock = core.Clock()

def send_marker(code):
    """Push marker to LSL stream. Returns LSL timestamp."""
    ts = local_clock()
    outlet.push_sample([code], ts)
    print(f"[MARKER | exp={exp_clock.getTime():.3f}s | lsl={ts:.3f}] {code}")
    return ts

# ─────────────────────────────────────────
# PARAMETERS
# ─────────────────────────────────────────
N_BLOCKS         = 5
TRIALS_PER_BLOCK = 28       # 14 left + 14 right, shuffled

BASELINE_EO_SEC  = 120      # eyes open
BASELINE_EC_SEC  = 120      # eyes closed
BASELINE_FIX_SEC = 60       # fixation only

FIXATION_SEC     = 2.0      # trial fixation
CUE_SEC          = 2.0      # cue display
IMAGERY_SEC      = 4.0      # imagery (cue stays on)
REST_SEC         = 2.0      # rest after imagery
ITI_MIN          = 2.0      # inter-trial interval min
ITI_MAX          = 3.0      # inter-trial interval max


BREAK_MIN_SEC    = 30       # minimum enforced break

# ─────────────────────────────────────────
# STIMULI
# ─────────────────────────────────────────
fixation  = visual.TextStim(win, text="+",            color="white",  height=0.2)
left_cue  = visual.TextStim(win, text="← LEFT HAND",  color="cyan",   height=0.2)
right_cue = visual.TextStim(win, text="RIGHT HAND →",  color="yellow", height=0.2)
rt_circle = visual.Circle(win, radius=0.08, fillColor="white", lineColor="white")
msg_stim  = visual.TextStim(win, text="", color="white", wrapWidth=1.5, height=0.07)

# ─────────────────────────────────────────
# DATA STORAGE
# ─────────────────────────────────────────
all_data  = []
data_file = f"{exp_info['Participant ID']}_MI_75min.csv"
fieldnames = [
    "Block", "Trial", "MI_Label", "KSS",
    "Event", "Marker", "Time_lsl", "Wall_time",
    "Block_Start_lsl", "Block_End_lsl"
]

def log(block, trial, mi_label, kss, event_name, marker,
        block_start="", block_end=""):
    all_data.append({
        "Block":           block,
        "Trial":           trial,
        "MI_Label":        mi_label,
        "KSS":             kss,
        "Event":           event_name,
        "Marker":          marker,
        "Time_lsl":        local_clock(),
        "Wall_time":       time.time(),
        "Block_Start_lsl": block_start,
        "Block_End_lsl":   block_end
    })

def save_data():
    with open(data_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    print(f"[SAVED] {data_file}")

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def wait_redraw(duration_s, draw_fn):
    """Redraw each frame for duration_s using monotonic Clock."""
    t = core.Clock()
    while t.getTime() < duration_s:
        draw_fn()
        win.flip()

def show_instruction(text, wait_key="space"):
    msg_stim.text = text
    msg_stim.draw()
    win.flip()
    event.waitKeys(keyList=[wait_key])

# ─────────────────────────────────────────
# CONSENT
# ─────────────────────────────────────────
def consent():
    show_instruction(
        "INFORMED CONSENT\n\n"
        "You are invited to participate in a study involving EEG\n"
        "recording during motor imagery tasks.\n\n"
        "Your participation is voluntary. You may stop at any time.\n\n"
        "Press SPACE to agree and continue."
    )

# ─────────────────────────────────────────
# INSTRUCTIONS
# ─────────────────────────────────────────
def instructions():
    show_instruction(
        "INSTRUCTIONS\n\n"
        "MOTOR IMAGERY\n"
        "  When ← or → appears, FEEL the movement of that hand.\n"
        "  Do NOT actually move it.\n\n"
        "REACTION TIME\n"
        "  Press SPACE as fast as possible when a white circle appears.\n\n"
        "KSS RATING\n"
        "  After each block, press a key from 1 to 9 to rate sleepiness.\n\n"
        "Press SPACE to start the experiment."
    )

# ─────────────────────────────────────────
# BASELINE  (EO 2min | EC 2min | Fixation 1min)
# ─────────────────────────────────────────
def baseline():
    show_instruction(
        "BASELINE — Eyes OPEN\n\n"
        "Stare at the cross. Relax. Stay still.\n"
        "Duration: 2 minutes.\n\n"
        "Press SPACE to start."
    )
    send_marker(1000)
    wait_redraw(BASELINE_EO_SEC, lambda: fixation.draw())

    show_instruction(
        "BASELINE — Eyes CLOSED\n\n"
        "Close your eyes and relax.\n"
        "Duration: 2 minutes.\n\n"
        "Press SPACE to start."
    )
    send_marker(1001)
    t = core.Clock()
    while t.getTime() < BASELINE_EC_SEC:
        win.flip()

    show_instruction(
        "BASELINE — Fixation\n\n"
        "Stare at the cross.\n"
        "Duration: 1 minute.\n\n"
        "Press SPACE to start."
    )
    send_marker(1002)
    wait_redraw(BASELINE_FIX_SEC, lambda: fixation.draw())
    send_marker(1003)   # baseline end

# ─────────────────────────────────────────
# MI TRIAL
# Fixation(2s) → Cue(2s) → Imagery/4s cue visible → Rest(2s) → ITI(2-3s)
# ─────────────────────────────────────────
def _run_mi_trial(hand, block_id, trial_id, block_start, record=True):

    # Fixation
    send_marker(10)
    wait_redraw(FIXATION_SEC, lambda: fixation.draw())

    # Cue
    cue_stim   = left_cue  if hand == "left" else right_cue
    cue_marker = 100       if hand == "left" else 101
    send_marker(cue_marker)
    wait_redraw(CUE_SEC, lambda: cue_stim.draw())

    # Imagery — cue stays on screen
    img_marker = 200 if hand == "left" else 201
    send_marker(img_marker)
    wait_redraw(IMAGERY_SEC, lambda: cue_stim.draw())

    # Rest
    send_marker(300)
    wait_redraw(REST_SEC, lambda: fixation.draw())

    # ITI (jittered blank)
    send_marker(400)
    t = core.Clock()
    while t.getTime() < random.uniform(ITI_MIN, ITI_MAX):
        win.flip()

    send_marker(11)  # trial end

    if record:
        log(block_id, trial_id, hand, "NA", "Trial_Complete",
            cue_marker, block_start=block_start)

# ─────────────────────────────────────────
# MI BLOCK  (28 trials, balanced L/R, ~6 min)
# ─────────────────────────────────────────
def mi_block(block_id):
    show_instruction(
        f"BLOCK {block_id} / {N_BLOCKS}\n\n"
        "← cyan   = LEFT HAND\n"
        "→ yellow  = RIGHT HAND\n\n"
        "Feel the movement. Stay still.\n\n"
        "Press SPACE to begin."
    )

    block_start = local_clock()
    send_marker(4000 + block_id)

    trial_order = ["left"] * 14 + ["right"] * 14
    random.shuffle(trial_order)

    for trial_id, hand in enumerate(trial_order, 1):
        _run_mi_trial(hand, block_id, trial_id, block_start, record=True)

    block_end = local_clock()
    send_marker(4100 + block_id)

    # Fill block_end for all trials in this block
    for row in all_data:
        if row["Block"] == block_id and row["Block_End_lsl"] == "":
            row["Block_End_lsl"] = block_end

    return block_start, block_end

# ─────────────────────────────────────────
# KSS RATING
# Simple: show 1-9 scale, wait for keypress, send marker
# Markers: 700 = KSS screen onset | 2001-2009 = rating value
# ─────────────────────────────────────────
def run_kss(block_id, block_start, block_end, final=False):

    # KSS screen onset marker
    onset_marker = 9000 if final else 700
    send_marker(onset_marker)
    log(block_id, "KSS_Onset", "NA", "NA", "KSS_Onset",
        onset_marker, block_start, block_end)

    # Simple 1-9 prompt — participant just presses a number
    msg_stim.text = (
        "How sleepy are you right now?\n\n"
        "1  ←  very alert                    very sleepy  →  9\n\n"
        "Press a key from 1 to 9"
    )
    msg_stim.draw()
    win.flip()

    # Wait for keypress
    keys = event.waitKeys(keyList=[str(k) for k in range(1, 10)])
    kss_value = int(keys[0])

    # Send rating marker  (e.g. rating 7 → marker 2007)
    rating_marker = 2000 + kss_value
    send_marker(rating_marker)
    log(block_id, "KSS_Rating", "NA", kss_value, "KSS_Response",
        rating_marker, block_start, block_end)

    print(f"[KSS] Block {block_id}: {kss_value}")

    # Brief confirmation on screen
    msg_stim.text = f"Recorded: {kss_value}"
    msg_stim.draw()
    win.flip()
    core.wait(0.8)

    return kss_value

# ─────────────────────────────────────────
# REACTION TIME TASK  (single trial per block)
# Fixation (random 2-5s) → white circle → SPACE response
# Markers: 30=fixation onset | 31=stimulus onset | 32=hit | 33=miss
# ─────────────────────────────────────────
def run_rt_task(block_id, block_start, block_end):

    # Fixation (random 2-5s — unpredictable onset)
    send_marker(30)
    log(block_id, 1, "NA", "NA", "RT_Fixation",
        30, block_start, block_end)
    isi = random.uniform(2.0, 5.0)
    wait_redraw(isi, lambda: fixation.draw())

    # Stimulus onset — white circle
    response_clock = core.Clock()
    rt_circle.draw()
    win.flip()
    response_clock.reset()   # start timer exactly at circle onset
    send_marker(31)
    log(block_id, 1, "NA", "NA", "RT_Stimulus",
        31, block_start, block_end)

    # Wait for SPACE (max 2s)
    keys = event.waitKeys(keyList=["space"], maxWait=2.0)

    if keys:
        rt_ms = response_clock.getTime() * 1000
        send_marker(32)
        log(block_id, 1, "NA", "NA", f"RT_Hit_{rt_ms:.1f}ms",
            32, block_start, block_end)
        print(f"[RT Block {block_id}] {rt_ms:.1f} ms")
    else:
        send_marker(33)
        log(block_id, 1, "NA", "NA", "RT_Miss",
            33, block_start, block_end)
        print(f"[RT Block {block_id}] MISS")

    # Blank screen 0.5s then continue
    win.flip()
    core.wait(0.5)

# ─────────────────────────────────────────
# INTER-BLOCK BREAK  (30s min, then self-paced)
# ─────────────────────────────────────────
def inter_block_break(block_id):
    send_marker(6000 + block_id)
    log(block_id, "Break_Start", "NA", "NA", "Break_Start",
        6000 + block_id)

    msg_stim.text = (
        f"End of Block {block_id}\n\n"
        "Take a short break. Relax, blink, stretch gently.\n\n"
        "(Minimum 30 s — then press SPACE to continue)"
    )
    msg_stim.draw()
    win.flip()
    core.wait(BREAK_MIN_SEC)
    event.waitKeys(keyList=["space"])

    send_marker(6100 + block_id)
    log(block_id, "Break_End", "NA", "NA", "Break_End",
        6100 + block_id)

# ─────────────────────────────────────────
# MAIN FLOW
# ─────────────────────────────────────────
def run():
    try:
        exp_clock.reset()

        # Phase 1 — Setup
        consent()
        instructions()

        # Phase 2 — Baseline
        baseline()

        # Phase 3 — 6 MI Blocks
        for block_id in range(1, N_BLOCKS + 1):
            block_start, block_end = mi_block(block_id)
            run_kss(block_id, block_start, block_end)
            run_rt_task(block_id, block_start, block_end)
            if block_id < N_BLOCKS:
                inter_block_break(block_id)

        # Phase 4 — Final KSS + debrief
        send_marker(9000)
        run_kss(block_id=0, block_start=0, block_end=0, final=True)

        send_marker(9999)
        show_instruction(
            "EXPERIMENT COMPLETE\n\n"
            "Thank you for your participation!\n\n"
            "Please wait for the experimenter.\n\n"
            "Press SPACE to exit."
        )

    except Exception as e:
        print(f"[ERROR] {e}")
        raise

    finally:
        save_data()
        win.close()
        core.quit()

run()
