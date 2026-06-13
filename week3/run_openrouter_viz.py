import os
from dotenv import load_dotenv

load_dotenv(override=True)
from visualizer import TokenPredictor, create_token_graph, visualize_predictions

model = "nvidia/nemotron-3-ultra-550b-a55b:free"
base_url = "https://openrouter.ai/api/v1"
api_key = os.getenv("OPENROUTER_API_KEY")

predictor = TokenPredictor(model, base_url=base_url, api_key=api_key)
predictions = predictor.predict_tokens("Life is", max_tokens=20)
print(f"Got {len(predictions)} predictions")
for p in predictions:
    token_repr = repr(p["token"])
    prob = p["probability"]
    alts = p["alternatives"]
    print(f"  {token_repr:20s} prob={prob:.3f}  alts={alts}")

G = create_token_graph(model, predictions)
plt = visualize_predictions(G, figsize=(14, 20))
plt.savefig("openrouter_viz.png", bbox_inches="tight", dpi=100)
plt.close()
print("Saved to week3/openrouter_viz.png")
