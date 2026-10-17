"""scripts/dev/loadenv.py: .env values reach a shell as data, never as code."""
import subprocess
import sys

from wasel.paths import ROOT

LOADER = ROOT / "scripts" / "dev" / "loadenv.py"


def _run_in_shell(tmp_path, env_text, snippet, *args):
    (tmp_path / ".env").write_text(env_text, encoding="utf-8")
    cmd = f'eval "$({sys.executable} {LOADER} {" ".join(args)})"; {snippet}'
    return subprocess.run(["bash", "-euc", cmd], cwd=tmp_path, capture_output=True, text=True)


def test_dollar_and_command_substitution_are_not_evaluated(tmp_path):
    pwned = tmp_path / "pwned"
    env = (f"X=$(touch {pwned})\nADMIN_TOKEN=abcdefghijklmnopqrstuvwx$yz12345678\nY=`touch {pwned}`\n"
           "Z='it'\"'\"'s $HOME'\nQ=\"two words\"\n")
    r = _run_in_shell(tmp_path, env, 'printf "%s|%s|%s|%s" "$ADMIN_TOKEN" "$X" "$Y" "$Q"')
    assert r.returncode == 0, r.stderr
    assert not pwned.exists()
    assert r.stdout == f"abcdefghijklmnopqrstuvwx$yz12345678|$(touch {pwned})|`touch {pwned}`|two words"


def test_app_and_shell_see_the_same_value(tmp_path):
    from dotenv import dotenv_values
    env = "A=plain\nB='single $x'\nC=\"double $x\"\nD=with # comment\n"
    r = _run_in_shell(tmp_path, env, 'printf "%s|%s|%s|%s" "$A" "$B" "$C" "$D"')
    seen = dotenv_values(tmp_path / ".env")
    assert r.stdout == "|".join(seen[k] for k in "ABCD")


def test_prefix_and_missing_file(tmp_path):
    r = _run_in_shell(tmp_path, "MODEL=m1\n", 'echo "${DOTENV_MODEL}"', "--prefix DOTENV_")
    assert r.stdout.strip() == "m1"
    (tmp_path / ".env").unlink()
    assert subprocess.run([sys.executable, str(LOADER)], cwd=tmp_path, capture_output=True, text=True).stdout == ""
