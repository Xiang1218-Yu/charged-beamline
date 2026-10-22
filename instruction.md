# 带电粒子束线模拟器

修复 `environment/beamline_sim` 中的 Python 程序。入口：

```bash
python3 -m beamline_sim --input INPUT.json --output OUTPUT.json
```

输入对象包含：

- `particles`：非空数组；每项有唯一非空字符串 `id`、正有限数 `mass`、非零有限数 `charge`、长度为 2 的有限数 `position` 和 `velocity`。
- `electric_field`：长度为 2 的有限数数组 `[Ex,Ey]`。
- `magnetic_field`：有限数 `Bz`，垂直于模拟平面。
- `dt`：正有限数；`steps`：非负整数，布尔值不能冒充整数。
- `aperture_radius`：正有限数。粒子初始位置必须严格位于该圆内。

每一步对仍存活的粒子使用二维 Boris 推进：先以半步电场加速，随后按 `t=q*Bz*dt/(2*m)` 在平面内旋转速度，再以另一个半步电场加速，最后用旋转后的速度推进位置。对正电荷和正 `Bz`，初速沿 +x 的粒子速度应朝 -y 偏转；反转电荷或磁场会反转偏转方向。纯磁场不得改变单粒子速度大小。

位置更新后，若粒子到原点的距离大于或等于孔径半径，它在该步被吸收：从后续步和最终 `particles` 移除，并在 `losses` 中记录 `{ "id": ..., "step": ... }`。同一步损失按 `id` 字典序排列；最终存活粒子也按 `id` 字典序排列。输入排列不得改变输出。

成功输出 JSON：`status` 为 `"ok"`，`time` 为 `steps*dt`，并包含最终 `particles`、`losses` 和 `diagnostics`。诊断量来自最终存活粒子：动能 `sum(0.5*m*v^2)`、二维机械动量 `sum(m*v)`、总电荷及存活粒子数。

任何结构错误、缺失字段、重复 ID、布尔值伪装数值、非有限数、非法范围或孔径外初态都必须拒收。拒收时退出码非零、标准错误以 `INPUT_ERROR:` 开头、已有输出文件逐字节不变，且不得遗留临时文件。成功写入必须采用同目录原子替换，输出为 UTF-8 JSON。
