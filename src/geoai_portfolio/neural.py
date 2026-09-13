"""Short, reproducible ResNet adaptation; no test-set model selection."""

import copy
import os
import random
import time

import numpy as np
import pandas as pd


def device_name(requested="auto"):
    import torch

    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested not in {"cpu", "cuda"}:
        raise ValueError("Device must be auto, cpu, or cuda")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable; install the cuda extra or choose cpu")
    return requested


def seed_everything(seed=42):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False


def make_loaders(dataset, batch_size=32):
    import torch
    from torch.nn import functional as F
    from torch.utils.data import DataLoader, TensorDataset

    rgb = dataset.images[:, [3, 2, 1]].astype("float32") / 10000
    train = dataset.mask("train")
    mean = rgb[train].mean(axis=(0, 2, 3), keepdims=True)
    std = rgb[train].std(axis=(0, 2, 3), keepdims=True).clip(1e-6)
    normalized = torch.from_numpy((rgb - mean) / std)
    resized = F.interpolate(normalized, size=(128, 128), mode="bilinear", align_corners=False)
    labels = torch.as_tensor(dataset.samples.label.to_numpy(), dtype=torch.long)
    loaders = {}
    for split in ["train", "val", "test"]:
        selected = dataset.mask(split)
        loaders[split] = DataLoader(
            TensorDataset(resized[selected], labels[selected]),
            batch_size=batch_size,
            shuffle=split == "train",
            num_workers=0,
            generator=torch.Generator().manual_seed(42),
        )
    return loaders, {
        "mean": mean.ravel().tolist(),
        "std": std.ravel().tolist(),
        "fitted_on": "train",
        "bands": ["B04", "B03", "B02"],
        "resize": 128,
    }


def initialize_model():
    import torch
    from torchvision.models import ResNet18_Weights, resnet18

    weights = ResNet18_Weights.IMAGENET1K_V1
    model = resnet18(weights=weights, progress=False)
    for parameter in model.parameters():
        parameter.requires_grad = False
    model.fc = torch.nn.Linear(model.fc.in_features, 10)
    for parameter in model.layer4.parameters():
        parameter.requires_grad = True
    return model


def infer(model, loader, device):
    import torch

    model.eval()
    outputs, truths = [], []
    with torch.inference_mode():
        for images, labels in loader:
            outputs.append(model(images.to(device)).softmax(1).cpu().numpy())
            truths.extend(labels.numpy())
    return np.concatenate(outputs), np.asarray(truths)


def fine_tune(model, loaders, device, epochs=3):
    import torch
    from sklearn.metrics import f1_score

    if not 1 <= epochs <= 5:
        raise ValueError("This demonstration permits 1–5 epochs")
    model.to(device)
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=3e-4, weight_decay=1e-3
    )
    best_f1, best_state, history = -1, None, []
    for epoch in range(epochs):
        started = time.perf_counter()
        # Keep frozen backbone and batch-normalization statistics stable on small batches.
        model.eval()
        losses = []
        for images, labels in loaders["train"]:
            optimizer.zero_grad(set_to_none=True)
            loss = torch.nn.functional.cross_entropy(model(images.to(device)), labels.to(device))
            loss.backward()
            optimizer.step()
            losses.append((loss.item(), len(labels)))
        probability, truth = infer(model, loaders["val"], device)
        val_f1 = f1_score(truth, probability.argmax(1), average="macro", zero_division=0)
        history.append(
            {
                "epoch": epoch + 1,
                "train_loss": sum(loss * n for loss, n in losses) / sum(n for _, n in losses),
                "validation_macro_f1": val_f1,
                "seconds": time.perf_counter() - started,
            }
        )
        if val_f1 > best_f1:
            best_f1, best_state = val_f1, copy.deepcopy(model.state_dict())
    model.load_state_dict(best_state)
    return pd.DataFrame(history)
