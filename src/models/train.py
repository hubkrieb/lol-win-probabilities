import argparse
from utils import load_data, init_model



def train(model, X_train, X_test, y_train, y_test, verbose = False):   
    model.fit(X_train, y_train, eval_set = [(X_train, y_train), (X_test, y_test)], verbose = verbose)
    return model

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_path', type = str, help = 'path of the dataset')
    parser.add_argument('--pretrained_model_path', type = str, help = 'path to the existing pretrained model', default = None)
    parser.add_argument('--model_path', type = str, help = 'path to save the resulting model')
    parser.add_argument('--test_size', type = float, help = 'ratio of the dataset used for test', default = 0.2)

    args = parser.parse_args()
    dataset_path, pretrained_model_path, model_path, test_size = args.dataset_path, args.pretrained_model_path, args.model_path, args.test_size

    X_train, X_test, y_train, y_test = load_data(dataset_path, test_size)
    model = init_model(pretrained_model_path)
    model = train(model, X_train, X_test, y_train, y_test, verbose = True)
    model.save_model(model_path)