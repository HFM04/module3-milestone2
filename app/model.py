import joblib
from pathlib import Path
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


def main():
    data = load_iris()
    X = data.data
    y = data.target
    target_names = data.target_names.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = Pipeline(steps=[
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=200,
            random_state=42,
            solver="lbfgs"   # explicit
        ))
    ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test accuracy: {acc:.3f}")
    print(classification_report(y_test, y_pred, target_names=target_names))

    artifact = {
        "model": model,
        "target_names": target_names,
        "model_version": "v1"
    }

    out_path = Path(__file__).resolve().parent / "model.pkl"
    joblib.dump(artifact, out_path)
    print(f"Saved model artifact to {out_path}")


if __name__ == "__main__":
    main()
