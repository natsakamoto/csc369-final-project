import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import norm


df = pd.read_parquet("prep_for_model.parquet")

# regression
formula_main = """
helpful_votes ~ verified_purchase_int + log_review_words
             + C(star_rating) + C(product_category) + C(ym)
"""

model_main = smf.glm(
    formula=formula_main,
    data=df,
    family=sm.families.NegativeBinomial(),
    offset=df["log_total_votes"],
).fit(cov_type="HC3")

print(model_main.summary())

# one sided test
def one_sided_pval_greater(result, term):
    beta = result.params[term]
    se = result.bse[term]
    z = beta / se
    p_one = 1 - norm.cdf(z)
    return beta, se, z, p_one

for term in ["verified_purchase_int", "log_review_words"]:
    beta, se, z, p = one_sided_pval_greater(model_main, term)
    irr = np.exp(beta)
    print(f"\nTEST: {term} > 0")
    print(f"  beta={beta:.4f}, SE={se:.4f}, z={z:.3f}, one-sided p={p:.4g}")
    print(f"  IRR=exp(beta)={irr:.4f}  ({100*(irr-1):.2f}% change in expected helpful_votes)")