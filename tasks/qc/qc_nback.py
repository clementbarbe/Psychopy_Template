import os
import traceback
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


print("QC NBACK LOADED FROM:", __file__)


def _safe_float(x):
    try:
        if x is None:
            return np.nan
        x = float(x)
        if np.isfinite(x):
            return x
        return np.nan
    except Exception:
        return np.nan


def _norminv(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    try:
        from scipy.stats import norm
        return norm.ppf(p)
    except Exception:
        # Robust fallback without scipy; avoids divisions
        from numpy import sqrt
        try:
            from numpy import erfinv
        except Exception:
            # If numpy lacks erfinv, give up safely
            return np.nan
        return sqrt(2.0) * erfinv(2.0 * p - 1.0)


def _compute_sdt_from_counts(hit, miss, fa, cr):
    hit = int(hit); miss = int(miss); fa = int(fa); cr = int(cr)
    n_signal = hit + miss
    n_noise = fa + cr
    if n_signal == 0 or n_noise == 0:
        return np.nan, np.nan, np.nan, np.nan

    hr = (hit + 0.5) / (n_signal + 1.0)
    far = (fa + 0.5) / (n_noise + 1.0)

    zhr = _norminv(hr)
    zfar = _norminv(far)
    if not np.isfinite(zhr) or not np.isfinite(zfar):
        return _safe_float(hr), _safe_float(far), np.nan, np.nan

    dprime = zhr - zfar
    criterion = -0.5 * (zhr + zfar)
    return _safe_float(hr), _safe_float(far), _safe_float(dprime), _safe_float(criterion)


def qc_nback(csv_path):
    try:
        if not os.path.exists(csv_path):
            print(f"QC Error: Fichier non trouvé {csv_path}")
            return

        print(f"--- QC N-Back (Post-Proc): {os.path.basename(csv_path)} ---")

        df = pd.read_csv(csv_path)

        qc_dir = os.path.join(os.path.dirname(csv_path), 'qc')
        os.makedirs(qc_dir, exist_ok=True)

        # Harmonisation N level
        if 'N_level' in df.columns:
            ncol = 'N_level'
        elif 'block_N_level' in df.columns:
            df['N_level'] = df['block_N_level']
            ncol = 'N_level'
        else:
            ncol = None

        # increm
        if 'is_increm' in df.columns:
            is_inc = bool(df['is_increm'].iloc[0])
        elif 'is_increasing' in df.columns:
            is_inc = bool(df['is_increasing'].iloc[0])
        else:
            is_inc = False
        mode_str = "Progressif (Blocs)" if is_inc else "Fixe"

        # drift
        if 'onset_time' in df.columns and 'onset_goal' in df.columns:
            df['onset_time'] = pd.to_numeric(df['onset_time'], errors='coerce')
            df['onset_goal'] = pd.to_numeric(df['onset_goal'], errors='coerce')
            df['drift_ms'] = (df['onset_time'] - df['onset_goal']) * 1000.0
            print("QC Info: Drift calculé avec succès.")
        else:
            df['drift_ms'] = np.nan

        # types
        if 'trial_number' in df.columns:
            df['trial_number'] = pd.to_numeric(df['trial_number'], errors='coerce')

        if 'rt' in df.columns:
            df['rt'] = pd.to_numeric(df['rt'], errors='coerce')

        if 'is_target' in df.columns:
            if df['is_target'].dtype != bool:
                df['is_target'] = df['is_target'].astype(str).str.lower().map(
                    {'true': True, 'false': False, '1': True, '0': False}
                )
            df['is_target'] = df['is_target'].fillna(False).astype(bool)

        if 'accuracy' in df.columns:
            df['accuracy'] = pd.to_numeric(df['accuracy'], errors='coerce')

        if 'status' not in df.columns:
            df['status'] = "NA"

        df_resp = df[df['rt'].notna()].copy()

        colors_status = {'HIT': '#2ca02c', 'CR': '#1f77b4', 'MISS': '#d62728', 'FA': '#ff7f0e', 'NA': '#7f7f7f'}

        # ---- Figure
        plt.style.use('ggplot')
        fig, axes = plt.subplots(2, 3, figsize=(19, 11))
        fig.suptitle(
            f"QC Report: {os.path.basename(csv_path)}\nMode: {mode_str}",
            fontsize=14, fontweight='bold'
        )

        # 1) SDT counts
        ax = axes[0, 0]
        order = ['HIT', 'MISS', 'FA', 'CR']
        counts = df['status'].value_counts().reindex(order).fillna(0).astype(int)
        sns.barplot(x=counts.index, y=counts.values, ax=ax, palette=[colors_status[o] for o in counts.index])
        ax.set_title("1. Réponses Globales (SDT)")
        ax.set_xlabel("")
        ax.set_ylabel("Count")

        # 2) RT box (boxplot is more robust than violin across seaborn versions)
        ax = axes[0, 1]
        if not df_resp.empty and df_resp['status'].nunique() > 0:
            sns.boxplot(x='status', y='rt', data=df_resp, ax=ax, palette=colors_status)
            ax.axhline(0.150, color='red', linestyle='--', linewidth=1, alpha=0.7)
            ax.axhline(2.0, color='orange', linestyle='--', linewidth=1, alpha=0.7)
            ax.set_title("2. RT (boxplot) + seuils (150ms / 2s)")
            ax.set_xlabel("")
            ax.set_ylabel("RT (s)")
        else:
            ax.text(0.5, 0.5, "Aucune réponse", ha='center', va='center')
            ax.set_axis_off()

        # 3) d' + acc by N (simple lineplot; skip if impossible)
        ax = axes[0, 2]
        if ncol is not None:
            rows = []
            for n, dfn in df.groupby(ncol):
                hit = int((dfn['status'] == 'HIT').sum())
                miss = int((dfn['status'] == 'MISS').sum())
                fa = int((dfn['status'] == 'FA').sum())
                cr = int((dfn['status'] == 'CR').sum())
                hr, far, dprime, crit = _compute_sdt_from_counts(hit, miss, fa, cr)
                acc = _safe_float(dfn['accuracy'].mean()) if 'accuracy' in dfn.columns else np.nan
                targ = _safe_float(dfn['is_target'].mean()) if 'is_target' in dfn.columns else np.nan
                rows.append({'N': n, 'dprime': dprime, 'accuracy': acc, 'targ_ratio': targ, 'n': len(dfn)})

            perf = pd.DataFrame(rows).sort_values('N')
            if not perf.empty:
                ax.plot(perf['N'], perf['accuracy'], marker='o', label='Accuracy', color='#55a868')
                ax.plot(perf['N'], perf['dprime'], marker='o', label="d'", color='#4c72b0')
                ax2 = ax.twinx()
                ax2.plot(perf['N'], perf['targ_ratio'], marker='s', label='Target ratio', color='#c44e52')
                ax2.set_ylim(0, 1)
                ax.set_title("3. Perf par N")
                ax.set_xlabel("N")
                ax.set_ylabel("Score")
                ax2.set_ylabel("Target ratio")
                # legend merge
                l1, lab1 = ax.get_legend_handles_labels()
                l2, lab2 = ax2.get_legend_handles_labels()
                ax.legend(l1 + l2, lab1 + lab2, fontsize=9, loc='upper left')
            else:
                ax.text(0.5, 0.5, "Pas de perf par N", ha='center', va='center')
                ax.set_axis_off()
        else:
            ax.text(0.5, 0.5, "N manquant", ha='center', va='center')
            ax.set_axis_off()

        # 4) Drift
        ax = axes[1, 0]
        if df['drift_ms'].notna().any() and df['trial_number'].notna().any():
            d = df[['trial_number', 'drift_ms']].dropna().sort_values('trial_number')
            ax.plot(d['trial_number'], d['drift_ms'], marker='o', color='#d62728')
            tol = 17.0
            ax.axhline(0, color='black', linestyle='--', linewidth=1)
            ax.axhspan(-tol, tol, color='green', alpha=0.12)
            p_out = (d['drift_ms'].abs() > tol).mean() * 100.0
            ax.set_title(f"4. Drift (>{tol:.0f}ms: {p_out:.1f}%)")
            ax.set_xlabel("Trial")
            ax.set_ylabel("Drift (ms)")
        else:
            ax.text(0.5, 0.5, "Drift non calculable", ha='center', va='center')
            ax.set_axis_off()

        # 5) RT by N (median)
        ax = axes[1, 1]
        if ncol is not None and not df_resp.empty:
            tmp = df_resp.copy()
            tmp['N'] = tmp[ncol]
            # medians by N
            med = tmp.groupby('N')['rt'].median().reset_index()
            ax.plot(med['N'], med['rt'], marker='o', color='#4c72b0')
            ax.set_title("5. RT médiane par N")
            ax.set_xlabel("N")
            ax.set_ylabel("RT (s)")
        else:
            ax.text(0.5, 0.5, "RT/N insuffisants", ha='center', va='center')
            ax.set_axis_off()

        # 6) Summary table
        ax = axes[1, 2]
        ax.set_title("6. Résumé par N")
        ax.axis('off')
        if ncol is not None:
            rows = []
            for n, dfn in df.groupby(ncol):
                hit = int((dfn['status'] == 'HIT').sum())
                miss = int((dfn['status'] == 'MISS').sum())
                fa = int((dfn['status'] == 'FA').sum())
                cr = int((dfn['status'] == 'CR').sum())
                hr, far, dprime, crit = _compute_sdt_from_counts(hit, miss, fa, cr)

                rts = pd.to_numeric(dfn['rt'], errors='coerce')
                med_rt = float(np.nanmedian(rts)) if rts.notna().any() else np.nan
                resp_pct = float(rts.notna().mean() * 100.0) if len(dfn) else np.nan

                targ_pct = float(dfn['is_target'].mean() * 100.0) if 'is_target' in dfn.columns and len(dfn) else np.nan

                drift = dfn['drift_ms']
                drift_mu = float(drift.mean()) if drift.notna().any() else np.nan

                rows.append([
                    int(n), len(dfn),
                    f"{targ_pct:.0f}%" if np.isfinite(targ_pct) else "NA",
                    f"{dprime:.2f}" if np.isfinite(dprime) else "NA",
                    f"{crit:.2f}" if np.isfinite(crit) else "NA",
                    f"{med_rt:.3f}" if np.isfinite(med_rt) else "NA",
                    f"{resp_pct:.0f}%" if np.isfinite(resp_pct) else "NA",
                    f"{drift_mu:.1f}" if np.isfinite(drift_mu) else "NA",
                ])

            rows = sorted(rows, key=lambda x: x[0])
            cols = ["N", "n", "Target%", "d'", "c", "RTmed", "Resp%", "Driftµ(ms)"]
            table = ax.table(cellText=rows, colLabels=cols, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1.0, 1.4)
        else:
            ax.text(0.5, 0.5, "N manquant", ha='center', va='center')

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        png_name = os.path.basename(csv_path).replace('.csv', '_QC.png')
        save_path = os.path.join(qc_dir, png_name)
        plt.savefig(save_path, dpi=120)
        plt.close()
        print(f"QC Terminé. Image sauvegardée : {save_path}")

    except Exception as e:
        print("QC ERROR:", repr(e))
        traceback.print_exc()
        raise