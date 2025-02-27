import math

def classify_news(probability_real, model_entropy, user_votes,
                  w_ai_base=0.5, w_user_base=0.5, min_votes=1,
                  threshold_real=0.34, threshold_fake=-0.34):
    """
    Combines AI model output and user votes to produce a final classification.

    Parameters:
        probability_real: float in [0, 1] - AI's softmax probability for "real".
        model_entropy: float - Entropy of the AI model's softmax output.
        user_votes: list of dicts - Each dict should have keys 'vote_value' and 'credibility'.
                    'vote_value' should be 1 (real) or 0 (fake), and credibility is a float.
        w_ai_base: float - Base weight for the AI component.
        w_user_base: float - Base weight for the user evaluation component.
        min_votes: int - Minimum number of user votes required to include user input.
        threshold_real: float - If Final_Score >= threshold_real, classify as "Real".
        threshold_fake: float - If Final_Score <= threshold_fake, classify as "Fake".

    Returns:
        final_score: float in [-1, 1]
        classification: string ("Real", "Fake", or "Not Sure")
    """
    # Step 1: Compute the AI Component
    # Map probability to [-1, +1]
    model_score = 2 * probability_real - 1

    # Compute AI confidence using entropy (max entropy for binary is ln(2))
    ai_confidence = 1 - (model_entropy / math.log(2))

    # Effective AI weight
    w_ai = w_ai_base * ai_confidence

    # Step 2: Compute the User Evaluation Component
    if len(user_votes) < min_votes:
        # Not enough user votes: use AI output only.
        final_score = model_score
    else:
        user_sum = 0.0
        total_cred = 0.0
        # Loop over user votes and calculate weighted sum and total credibility
        for vote in user_votes:
            # Map vote_value: 1 -> +1, 0 -> -1
            v = 1 if vote['vote_value'] == 1 else -1
            cred = vote['credibility']
            user_sum += cred * v
            total_cred += cred

        # Avoid division by zero; if no credibility exists, default to AI output.
        if total_cred == 0:
            raw_user_score = 0
        else:
            raw_user_score = user_sum / total_cred  # Range: [-1, +1]

        # Compute credibility-weighted proportions for "real" and "fake"
        sum_cred_real = 0.0
        sum_cred_fake = 0.0
        for vote in user_votes:
            cred = vote['credibility']
            if vote['vote_value'] == 1:
                sum_cred_real += cred
            else:
                sum_cred_fake += cred

        p_r = sum_cred_real / total_cred
        p_f = sum_cred_fake / total_cred

        # Compute user vote entropy; avoid math domain error by checking p_r and p_f > 0
        user_entropy = 0.0
        if p_r > 0:
            user_entropy -= p_r * math.log(p_r)
        if p_f > 0:
            user_entropy -= p_f * math.log(p_f)

        normalized_entropy = user_entropy / math.log(2)  # ln(2) is max entropy for binary
        vote_confidence = 1 - normalized_entropy

        # Effective user weight, dynamically adjusted by vote confidence
        w_user = w_user_base * vote_confidence

        # Step 3: Normalize the weights (so that they sum to 1)
        total_w = w_ai + w_user
        normalized_w_ai = w_ai / total_w
        normalized_w_user = w_user / total_w

        # Step 4: Compute the Final Score (weighted combination)
        final_score = (normalized_w_ai * model_score) + (normalized_w_user * raw_user_score)

    # Step 5: Classify the Outcome based on final_score thresholds
    if final_score >= threshold_real:
        classification = "Real"
    elif final_score <= threshold_fake:
        classification = "Fake"
    else:
        classification = "Not Sure"

    return final_score, classification

