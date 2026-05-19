import joblib
import mlflow
import pandas as pd
import lightgbm as lgb

class AVM(mlflow.pyfunc.PythonModel):

    def load_context(self, context):
        self.preprocessor = joblib.load(context.artifacts["preprocessor"])
        self.booster = lgb.Booster(model_file=context.artifacts["booster"])

    def predict(self, context, model_input: pd.DataFrame) -> pd.Series:
        df = self.preprocessor.transform_batch(model_input)
        return pd.Series(10 ** self.booster.predict(df))
