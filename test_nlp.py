from collections import Counter

doc1 = " I don’t want to go A groovy king of love You can’t hurry love This must be love Take me with you"
doc2 = "All out of love Here i am I remember love Love is all Don’t tell me "


def LM(doc):
    text = doc.lower().split()
    total = len(text)
    #     print(total)

    results = Counter(text).most_common()
    #     print(results)

    results_final = []
    for i in range(len(results)):
        results_final.append((results[i][0], '{}/{}'.format(results[i][1], total)))
    print(results_final)

    return results

LM(doc1)
LM(doc2)
LM(doc2+doc1)

tokens_len_d1, tokens_len_d2 = len(doc1.split()), len(doc2.split())
tokens_len_all = tokens_len_d1 + tokens_len_d2
lm_d1, lm_d2 = Counter(doc1.split()), Counter(doc2.split())
lm_all = lm_d1 + lm_d2


def count_ranking(LM, tokens_len, query, delta=0.5):
    ranking = 0
    for term in query.split():
        p = (1 - delta) * (LM[term] / tokens_len) \
            + delta * (lm_all[term] / tokens_len_all)
        ranking = p if ranking == 0 else ranking * p
    return ranking

query_text = "i remember you"
print("P(Q|d1): ", count_ranking(lm_d1, tokens_len_d1, query_text))
print("P(Q|d2): ", count_ranking(lm_d2, tokens_len_d2, query_text))

