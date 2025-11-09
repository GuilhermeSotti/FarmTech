import time
from app.controllers.fase3.simulate_iot_controller import main as simulate_main

def test_simulate_runs():
    # apenas garante que roda sem exceção (não é ideal para unit test)
    simulate_main()
    assert True
