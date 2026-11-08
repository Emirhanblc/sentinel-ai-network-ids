from data.export_figures import confusion_matrix_svg, export_confusion_matrix


def test_confusion_matrix_svg_contains_labels_and_counts(tmp_path) -> None:
    svg = confusion_matrix_svg([[12, 1], [0, 9]], ["Temiz", "DDoS"])
    assert "Temiz" in svg
    assert "DDoS" in svg
    assert ">12<" in svg
    output = tmp_path / "matrix.svg"
    metrics = tmp_path / "metrics.json"
    metrics.write_text(
        '{"confusion_matrix": [[12, 1], [0, 9]], "labels": ["Temiz", "DDoS"]}',
        encoding="utf-8",
    )
    export_confusion_matrix(metrics, output)
    assert output.is_file()
    assert "Karışıklık matrisi" in output.read_text(encoding="utf-8")
