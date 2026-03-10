import argparse
import os
from pathlib import Path

import torch

from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.diffusion.sample import sample_latents
from shap_e.models.download import load_config, load_model
from shap_e.util.notebooks import decode_latent_mesh


def generate_ply_from_text(
    prompt: str,
    output_dir: str = "outputs",
    batch_size: int = 1,
    guidance_scale: float = 15.0,
    karras_steps: int = 64,
) -> str:
    """
    generate the .ply file and return the path
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    xm = load_model("transmitter", device=device)
    model = load_model("text300M", device=device)
    diffusion = diffusion_from_config(load_config("diffusion"))

    latents = sample_latents(
        batch_size=batch_size,
        model=model,
        diffusion=diffusion,
        guidance_scale=guidance_scale,
        model_kwargs=dict(texts=[prompt] * batch_size),
        progress=True,
        clip_denoised=True,
        use_fp16=torch.cuda.is_available(),
        use_karras=True,
        karras_steps=karras_steps,
        sigma_min=1e-3,
        sigma_max=160,
        s_churn=0,
    )

    os.makedirs(output_dir, exist_ok=True)

    # 目前只用第一个 latent，生成一个 .ply 网格
    latent = latents[0]
    tri_mesh = decode_latent_mesh(xm, latent).tri_mesh()

    out_path = Path(output_dir) / "shap_e_mesh_0.ply"
    with open(out_path, "wb") as f:
        tri_mesh.write_ply(f)

    return str(out_path)


def main():
    parser = argparse.ArgumentParser(
        description="使用 Shap-E 从文本生成 3D 网格（.ply）。"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="文本描述，例如：一棵秋天的红枫树",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="保存生成 .ply 文件的目录（默认：outputs）",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="一次采样多少个 latent，一般 1 即可。",
    )
    parser.add_argument(
        "--guidance-scale",
        type=float,
        default=15.0,
        help="Classifier-free guidance 系数，数值越大越贴合文本，但也可能失真。",
    )
    parser.add_argument(
        "--karras-steps",
        type=int,
        default=64,
        help="Karras 采样步数，步数越多质量越好但越慢。",
    )

    args = parser.parse_args()

    ply_path = generate_ply_from_text(
        prompt=args.prompt,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        guidance_scale=args.guidance_scale,
        karras_steps=args.karras_steps,
    )
    print(f"generated:{ply_path}")


if __name__ == "__main__":
    main()

