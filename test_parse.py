import parse

def test_main():
    parse.main({'file_in': 'input_file.txt', 'file_out': 'test_output.txt'})
    expected = open("expected_output.txt").read()
    given = open("test_output.txt").read()
    assert expected == given, "Expected and given outputs are not equal."
