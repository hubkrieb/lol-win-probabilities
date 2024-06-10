import argparse
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from utils import load_data, init_model

#TO DO: Add accuracy -x for x minutes before the end of the game

def eval(model, X_test, y_test):
    y_pred = model.predict(X_test)
    res = {}
    res['accuracy'] = accuracy_score(y_test, y_pred)
    res['f1'] = f1_score(y_test, y_pred)
    res['roc auc'] = roc_auc_score(y_test, y_pred)
    for i in range(0, 35, 5):
        res[f'accuracy@{i}'] = accuracy_score_at(X_test, y_test, y_pred, i)
    return res

def accuracy_score_at(X_test, y_true, y_pred, minute):
    ind = X_test.reset_index()[X_test.reset_index()['minute'] == minute].index
    return accuracy_score(y_true.reset_index(drop = True).iloc[ind], y_pred[ind])

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_path', type = str, help = 'path of the data')
    parser.add_argument('--model_path', type = str, help = 'path to the model')
    parser.add_argument('--test_size', type = float, help = 'ratio of the dataset used for test', default = 0.2)

    args = parser.parse_args()
    dataset_path, model_path, test_size = args.dataset_path, args.model_path, args.test_size

    X_test, y_test = load_data(dataset_path, test_size)
    model = init_model(model_path)
    results = eval(model, X_test, y_test)

    for metric, value in results.items():
        print(metric + ' :', round(value, 3))