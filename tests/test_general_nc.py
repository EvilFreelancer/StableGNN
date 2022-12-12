import collections
from datetime import datetime

import numpy as np
import torch
import torch_geometric.transforms as T
from torch_geometric.utils import to_dense_adj

from stable_gnn.explain import Explain
from stable_gnn.graph import Graph
from tutorials.train_model_pipeline import TrainModelNC, TrainModelOptunaNC

dt = datetime.now()

name = "texas"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
adjust_flag = False

ssl_flag = False
root = "../data_validation/"
####

data = Graph(name, root=root + str(name), transform=T.NormalizeFeatures(), adjust_flag=adjust_flag)[0]
assert (max(float(data.edge_index[0].max()), float(data.edge_index[1].max())) + 1) == len(data.x) == data.num_nodes
assert len(collections.Counter((data.y).tolist())) == 5
assert data.x.shape[1] == 1703

#######
train_flag = False
if train_flag:
    optuna_training = TrainModelOptunaNC(
        data=data,
        dataset_name=name,
        device=device,
        ssl_flag=ssl_flag,
    )

    best_values = optuna_training.run(number_of_trials=3)
    model_training = TrainModelNC(
        data=data,
        dataset_name=name,
        device=device,
        ssl_flag=ssl_flag,
    )

    model, train_acc_mi, train_acc_ma, test_acc_mi, test_acc_ma = model_training.run(best_values)
    torch.save(model, "model.pt")

    assert train_acc_mi > test_acc_mi
    assert np.isclose(test_acc_mi, 0.6, atol=0.1)
    assert np.isclose(train_acc_mi, 0.9, atol=0.1)


model = torch.load("model.pt")
explain_flag = True
if explain_flag:
    features = np.load(root + name + "/X.npy")
    try:
        adj_matrix = np.load(root + name + "/A.npy")
    except:
        adj_matrix = torch.squeeze(to_dense_adj(data.edge_index.cpu())).numpy()

    explainer = Explain(model=model, adj_matrix=adj_matrix, features=features)

    pgm_explanation = explainer.structure_learning_bamt(34)
    assert len(pgm_explanation.nodes) >= 2
    assert len(pgm_explanation.edges) >= 1
    print("explanations is", pgm_explanation.nodes, pgm_explanation.edges)
