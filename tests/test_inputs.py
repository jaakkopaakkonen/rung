import taskgraph.inputs

def test_inputs():
    taskgraph.inputs.add_input_names("blah", ["alpha", "beta", "gamma"])
    assert taskgraph.inputs.is_input("alpha")
    assert taskgraph.inputs.is_input("blah_beta")
    assert taskgraph.inputs.is_input("blah.gamma")
    assert not taskgraph.inputs.is_input("blah")
    assert taskgraph.inputs.get_simple_values(
        "blah",
        {
                "blahalpha": "alphavalue",
                "blah.beta": "betavalue",
                "blah_gamma": "gammavalue"
                },
    ) == {
        "alpha": "alphavalue",
        "beta": "betavalue",
        "gamma": "gammavalue",
    }
    taskgraph.inputs.reset()