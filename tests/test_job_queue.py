from ulp_project.job_queue import create_job, load_job, load_job_result, write_job_result


def test_job_queue_writes_only_to_supplied_runtime_root(tmp_path):
    job = create_job({"point_id": "V001_pohon_sono"}, runtime_root=tmp_path)
    loaded = load_job(str(job["job_id"]), runtime_root=tmp_path)
    assert loaded["status"] == "QUEUED"
    write = write_job_result(str(job["job_id"]), {"status": "MODEL_NOT_READY_DRY_RESULT"}, runtime_root=tmp_path)
    assert write["status"] == "RESULT_WRITTEN"
    result = load_job_result(str(job["job_id"]), runtime_root=tmp_path)
    assert result["status"] == "MODEL_NOT_READY_DRY_RESULT"
