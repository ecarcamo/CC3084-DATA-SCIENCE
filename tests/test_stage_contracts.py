import inspect
import unittest

from pipeline import evaluation, model, monitoring, publish, tracking

CONTRACTS = {
    model: {
        "fit_and_forecast": ["series", "config"],
        "model_parameters": ["series", "config"],
    },
    evaluation: {
        "evaluate": ["series", "config"],
        "accept": ["checks", "estimates", "metrics", "config"],
    },
    tracking: {"log_run": ["metadata", "config", "artifacts_dir"]},
    monitoring: {"run_monitoring": ["series", "estimates", "checks", "previous_approved_dir", "config"]},
    publish: {
        "publish": ["candidate_dir", "config"],
        "latest_approved": ["config"],
        "restore": ["version_id", "config"],
    },
}


class StageContractTests(unittest.TestCase):
    def test_stage_modules_expose_agreed_signatures(self):
        for module, functions in CONTRACTS.items():
            for name, parameters in functions.items():
                with self.subTest(function=f"{module.__name__}.{name}"):
                    function = getattr(module, name)
                    self.assertTrue(callable(function))
                    self.assertEqual(list(inspect.signature(function).parameters), parameters)
                    self.assertTrue(inspect.getdoc(function))


if __name__ == "__main__":
    unittest.main()
