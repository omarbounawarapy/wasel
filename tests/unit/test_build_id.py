from wasel.settings import build_id


def test_explicit_git_sha_wins_over_render_and_git(tmp_path):
    env = {"RENDER_GIT_COMMIT": "b" * 40}
    assert build_id("abc1234", env=env, root=tmp_path) == "abc1234"


def test_render_commit_is_used_when_no_git_sha(tmp_path):
    assert build_id("", env={"RENDER_GIT_COMMIT": "f" * 40}, root=tmp_path) == "f" * 12


def test_no_checkout_and_no_env_is_dev(tmp_path):
    assert build_id("", env={}, root=tmp_path) == "dev"


def test_a_checkout_reports_its_head(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@example.com",
                    "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    head = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    assert build_id("", env={}, root=tmp_path) == head
