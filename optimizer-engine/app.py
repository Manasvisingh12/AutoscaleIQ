from flask import Flask, jsonify

from analyzer import (
    detect_underutilized_pods,
    detect_oversized_containers,
    detect_excess_replicas,
    detect_memory_waste
)

app = Flask(__name__)


@app.route("/")
def home():

    return "AutoScaleIQ Optimization Engine Running"


@app.route("/recommendations")
def recommendations():

    all_recommendations = []

    all_recommendations.extend(detect_underutilized_pods())

    all_recommendations.extend(detect_oversized_containers())

    all_recommendations.extend(detect_excess_replicas())

    all_recommendations.extend(detect_memory_waste())

    return jsonify(all_recommendations)


if __name__ == "__main__":

    app.run(debug=True)