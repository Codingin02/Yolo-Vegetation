from ulp_project.frame_size_guard import validate_frame_size
from ulp_project.origin_guard import check_origin
from ulp_project.rate_limit_policy import check_rate_limit
from ulp_project.session_token import token_git_policy


def test_remote_security_policies():
    assert validate_frame_size(2_000_000)["allowed"] is False
    assert check_rate_limit(100)["allowed"] is False
    assert check_origin(None)["allowed"] is True
    assert token_git_policy()["do_not_commit"] is True
