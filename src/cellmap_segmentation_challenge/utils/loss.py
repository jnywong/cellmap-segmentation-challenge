import torch


class CellMapLossWrapper(torch.nn.modules.loss._Loss):
    """
    Wrapper for any PyTorch loss function that is applied to the output of a model and the target.

    Because the target can contain NaN values, the loss function is applied only to the non-NaN values.
    This is done by multiplying the loss by a mask that is 1 where the target is not NaN and 0 where the target is NaN.
    The loss is then averaged across the non-NaN values.

    Parameters
    ----------
    loss_fn : torch.nn.modules.loss._Loss or torch.nn.modules.loss._WeightedLoss
        The loss function to apply to the output and target.
    **kwargs
        Keyword arguments to pass to the loss function.
    """

    def __init__(
        self,
        loss_fn: torch.nn.modules.loss._Loss | torch.nn.modules.loss._WeightedLoss,
        **kwargs,
    ):
        super().__init__()
        self.kwargs = kwargs
        self.kwargs["reduction"] = "none"
        self.loss_fn = loss_fn(**self.kwargs)

    def calc_loss(self, outputs: torch.Tensor, target: torch.Tensor):
        loss = self.loss_fn(outputs, target.nan_to_num(0))
        loss = (loss * target.isnan().logical_not()).nanmean()
        return loss

    def forward(
        self,
        outputs: dict | torch.Tensor,
        targets: dict | torch.Tensor,
    ):
        if isinstance(targets, dict):
            loss = 0
            if isinstance(outputs, dict):
                for key, target in targets.items():
                    loss += self.calc_loss(outputs[key], target)
            else:
                # Assumes outputs is a list or tuple of tensors aligned with targets
                for i, target in enumerate(targets.values()):
                    loss += self.calc_loss(outputs[i], target)
            loss /= len(targets)
        else:
            loss = self.calc_loss(outputs, targets)  # type: ignore
        return loss
