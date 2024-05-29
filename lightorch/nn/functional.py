import torch
from torch import nn, Tensor
from typing import Optional, Union, Tuple, Callable, List
import torch.nn.functional as F
from lightning.pytorch import LightningModule
from einops import rearrange


def _fourierconvNd(x: Tensor, weight: Tensor, bias: Tensor | None) -> Tensor:
    # weight -> 1, 1, out channels, *kernel_size
    x *= weight.reshape(1, 1, *weight.shape)  # Convolution in the fourier space

    if bias is not None:
        return x + bias.reshape(1, 1, -1, 1, 1)

    return x


def _fourierdeconvNd(
    x: Tensor, weight: Tensor, bias: Tensor | None, eps: float = 1e-5
) -> Tensor:
    # weight -> 1, 1, out channels, *kernel_size
    x /= weight.reshape(1, 1, *weight.shape) + eps  # Convolution in the fourier space

    if bias is not None:
        return x + bias.reshape(1, 1, -1, 1, 1)

    return x


def fourierconv3d(x: Tensor, one: Tensor, weight: Tensor, bias: Tensor | None):
    """
    x (Tensor): batch size, channels, height, width
    weight (Tensor): out channels, *kernel_size
    one (Tensor): out channels, in channels, *1 #Paralelization game
    bias (Tensor): out channels
    stride: (int)
    padding: (int)
    """
    if one is not None:
        # Augment the channel dimension of the input
        out = F.conv3d(x, one, None, 1)  # one: (out_channel, in_channel, *kernel_size)

    # Rearrange tensors for Fourier convolution
    out = rearrange(
        out,
        "B C (f kd) (h kh) (w kw) -> B (f h w) C kd kh kw",
        kd=weight.shape[-3],
        kh=weight.shape[-2],
        kw=weight.shape[-1],
    )

    out = _fourierconvNd(out, weight, bias)

    out = rearrange(out, "B (f h w) C kd kh kw -> B C (f kd) (h kh) (w kw)")

    return out


def fourierconv2d(x: Tensor, one: Tensor, weight: Tensor, bias: Tensor | None):
    """
    x (Tensor): batch size, channels, height, width
    weight (Tensor): out channels, *kernel_size
    one (Tensor): out channels, in channels, *1 #Paralelization game
    bias (Tensor): out channels
    stride: (int)
    padding: (int)
    """
    if one is not None:
        # Augment the channel dimension of the input
        out = F.conv2d(x, one, None, 1)  # one: (out_channel, in_channel, *kernel_size)

    out = rearrange(
        out,
        "B C (h k1) (w k2) -> B (h w) C k1 k2",
        k1=weight.shape[-2],
        k2=weight.shape[-1],
    )

    out = _fourierconvNd(out, weight, bias)

    out = rearrange(out, "B (h w) C k1 k2 -> B C (h k1) (w k2)")

    return out


def fourierconv1d(x: Tensor, one: Tensor, weight: Tensor, bias: Tensor | None):
    """
    x (Tensor): batch size, channels, sequence length
    weight (Tensor): out channels, kernel_size
    one (Tensor): out channels, in channels, *1 #Paralelization game
    bias (Tensor): out channels
    stride: (int)
    padding: (int)
    """
    if one is not None:
        # Augment the channel dimension of the input
        out = F.conv1d(x, one, None, 1)  # one: (out_channel, in_channel, *kernel_size)

    out = rearrange(out, "B C (l k) -> B l C k", k=weight.shape[-1])

    out = _fourierconvNd(out, weight, bias)

    out = rearrange(out, "B l C k -> B C (l k)")

    return out


def fourierdeconv3d(
    x: Tensor, one: Tensor, weight: Tensor, bias: Tensor | None, eps: float = 1e-5
):
    """
    x (Tensor): batch size, channels, height, width
    weight (Tensor): out channels, *kernel_size
    one (Tensor): out channels, in channels, *1 #Paralelization game
    bias (Tensor): out channels
    stride: (int)
    padding: (int)
    """
    if one is not None:
        # Augment the channel dimension of the input
        out = F.conv3d(x, one, None, 1)  # one: (out_channel, in_channel, *kernel_size)

    # Rearrange tensors for Fourier convolution
    out = rearrange(
        out,
        "B C (f kd) (h kh) (w kw) -> B (f h w) C kd kh kw",
        kd=weight.shape[-3],
        kh=weight.shape[-2],
        kw=weight.shape[-1],
    )

    out = _fourierdeconvNd(out, weight, bias, eps)

    out = rearrange(out, "B (f h w) C kd kh kw -> B C (f kd) (h kh) (w kw)")

    return out


def fourierdeconv2d(
    x: Tensor, one: Tensor, weight: Tensor, bias: Tensor | None, eps: float = 1e-5
):
    """
    x (Tensor): batch size, channels, height, width
    weight (Tensor): out channels, *kernel_size
    one (Tensor): out channels, in channels, *1 #Paralelization game
    bias (Tensor): out channels
    stride: (int)
    padding: (int)
    """
    if one is not None:
        # Augment the channel dimension of the input
        out = F.conv2d(x, one, None, 1)  # one: (out_channel, in_channel, *kernel_size)

    out = rearrange(
        out,
        "B C (h k1) (w k2) -> B (h w) C k1 k2",
        k1=weight.shape[-2],
        k2=weight.shape[-1],
    )

    out = _fourierdeconvNd(out, weight, bias, eps)

    out = rearrange(out, "B (h w) C k1 k2 -> B C (h k1) (w k2)")

    return out


def fourierdeconv1d(
    x: Tensor, one: Tensor, weight: Tensor, bias: Tensor | None, eps: float = 1e-5
):
    """
    x (Tensor): batch size, channels, sequence length
    weight (Tensor): out channels, kernel_size
    one (Tensor): out channels, in channels, *1 #Paralelization game
    bias (Tensor): out channels
    stride: (int)
    padding: (int)
    """
    if one is not None:
        # Augment the channel dimension of the input
        out = F.conv1d(x, one, None, 1)  # one: (out_channel, in_channel, *kernel_size)

    out = rearrange(out, "B C (l k) -> B l C k", k=weight.shape[-1])

    out = _fourierdeconvNd(out, weight, bias, eps)

    out = rearrange(out, "B l C k -> B C (l k)")

    return out


def _partialconvnd(
    conv: F,
    input: Tensor,
    mask_in: Tensor,
    weight: Tensor,
    one_sum: Tensor,
    bias: Optional[Tensor],
    stride,
    padding,
    dilation,
    update_mask: bool = True,
) -> Tuple[Tensor, Tensor] | Tensor:

    with torch.no_grad():
        sum_m: Tensor = conv(
            mask_in,
            torch.ones_like(weight, requires_grad=False),
            stride=stride,
            padding=padding,
            dilation=dilation,
        )
        if update_mask:
            updated_mask = sum_m.clamp_max(1)

    out = conv(input * mask_in, weight, None, stride, padding, dilation)

    out *= one_sum / sum_m
    out += bias

    return (out, updated_mask) if update_mask else out


def partialconv3d(
    input: Tensor,
    mask_in: Tensor,
    weight: Tensor,
    one_sum: int,
    bias: Optional[Tensor],
    stride,
    padding,
    dilation,
    update_mask: bool = True,
) -> Union[Tuple[Tensor, Tensor], Tensor]:

    return _partialconvnd(
        F.conv3d,
        input,
        mask_in,
        weight,
        one_sum,
        bias,
        stride,
        padding,
        dilation,
        update_mask,
    )


def partialconv2d(
    input: Tensor,
    mask_in: Tensor,
    weight: Tensor,
    one_sum: int,
    bias: Optional[Tensor],
    stride,
    padding,
    dilation,
    update_mask: bool = True,
) -> Union[Tuple[Tensor, Tensor], Tensor]:

    return _partialconvnd(
        F.conv2d,
        input,
        mask_in,
        weight,
        one_sum,
        bias,
        stride,
        padding,
        dilation,
        update_mask,
    )


def partialconv1d(
    input: Tensor,
    mask_in: Tensor,
    weight: Tensor,
    one_sum: int,
    bias: Optional[Tensor],
    stride,
    padding,
    dilation,
    update_mask: bool = True,
) -> Union[Tuple[Tensor, Tensor], Tensor]:

    return _partialconvnd(
        F.conv1d,
        input,
        mask_in,
        weight,
        one_sum,
        bias,
        stride,
        padding,
        dilation,
        update_mask,
    )


def residual_connection(
    x: Tensor,
    sublayer: Callable[[Tensor], Tensor],
    to_dim_layer: Callable[[Tensor], Tensor] = nn.Identity(),
) -> Tensor:
    return to_dim_layer(x) + sublayer(x)


# Criterion functionals


def psnr(input: Tensor, target: Tensor, max: float) -> Tensor:
    return 10 * torch.log10(
        torch.div(torch.pow(max, 2), torch.nn.functional.mse_loss(input, target))
    )


def style_loss(
    input: Tensor,
    target: Tensor,
    F_p: Tensor,
    feature_extractor: nn.Module | LightningModule = None,
) -> Tensor:
    if feature_extractor is not None:
        phi_input: Tensor = feature_extractor(input)
        phi_output: Tensor = feature_extractor(target)

    phi_input: List[Tensor] = change_dim(phi_input)
    phi_output: List[Tensor] = change_dim(phi_output)

    return ((_style_forward(phi_input, phi_output)) / F_p).sum()


def perceptual_loss(
    input: Tensor,
    target: Tensor,
    N_phi_p: Tensor,
    feature_extractor: nn.Module | LightningModule = None,
) -> Tensor:
    if feature_extractor is not None:
        phi_input: Tensor = feature_extractor(input)
        phi_output: Tensor = feature_extractor(target)
    return (
        Tensor(
            [
                torch.norm(phi_out - phi_gt, p=1)
                for phi_out, phi_gt in zip(
                    phi_input,
                    phi_output,
                )
            ]
        )
        / N_phi_p
    ).sum()


def change_dim(P: List[Tensor]) -> List[Tensor]:
    return [tensor.view(tensor.shape[0], tensor.shape[1], -1) for tensor in P]


def _style_forward(input_list: List[Tensor], gt_list: List[Tensor]) -> List[Tensor]:
    return Tensor(
        [
            torch.norm(out @ out.transpose(-2, -1) - gt @ gt.transpose(-2, -1), p=1)
            for out, gt in zip(input_list, gt_list)
        ]
    )


def total_variance(input: Tensor) -> Tensor:
    return torch.norm(input[:, :, :, :-1] - input[:, :, :, 1:], p=1).sum() + torch.norm(input[:, :, :-1, :] - input[:, :, 1:, :], p = 1).sum()


def kl_div(mu: Tensor, logvar: Tensor) -> Tensor:
    return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
