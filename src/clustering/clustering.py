import os
import numpy as np
import pandas as pd
import scipy.stats as stats
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE


class HierarchicalClusteringModel:
	def __init__(self):
		self.scaler1 = None
		self.kmeans1 = None
		self.scaler2 = None
		self.kmeans2 = None
		self.expert_cluster_id = None
		self.non_expert_cluster_id = None
		self.toxic_cluster_id = None
		self.casual_cluster_id = None

	def predict(self, ocean, helpfulness, sentiment_probs):
		"""
		Dự đoán nhóm khách hàng theo mô hình phân tầng:
		- Tầng 1: Tách Chuyên gia
		- Tầng 2: Tách Toxic và Qua đường dễ dãi
		"""
		p_tieucuc, p_tichcuc = sentiment_probs[0], sentiment_probs[2]
		conscientiousness = ocean[1]

		f_s1 = np.array([[helpfulness, conscientiousness]])
		f_s1_scaled = self.scaler1.transform(f_s1)
		pred_s1 = self.kmeans1.predict(f_s1_scaled)[0]

		if pred_s1 == self.expert_cluster_id:
			return "Nhóm 1: Chuyên gia đánh giá"

		neuroticism = ocean[4]
		f_s2 = np.array([[p_tieucuc, p_tichcuc, neuroticism]])
		f_s2_scaled = self.scaler2.transform(f_s2)
		pred_s2 = self.kmeans2.predict(f_s2_scaled)[0]

		if pred_s2 == self.toxic_cluster_id:
			return "Nhóm 2: Toxic / Khó tính"
		return "Nhóm 3: Người qua đường dễ dãi"


def main():
	root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
	data_path = os.path.join(root, "data", "clustering_final.csv")

	print("Dang doc tap du lieu tu he thong...")
	if not os.path.exists(data_path):
		raise FileNotFoundError(f"Khong tim thay file du lieu tai duong dan: {data_path}")

	df = pd.read_csv(data_path)
	df.columns = df.columns.str.strip()
	print(f"Da tai xong. Tong so luong mau ban dau: {len(df)} dong.")

	my_single_model = HierarchicalClusteringModel()

	# ============================================================
	# 1) TANG 1: Tach nhom Chuyen gia
	# ============================================================
	print("\n[TANG 1] Dang loc Nhom Chuyen gia bang Helpfulness va C...")

	stage1_features = ["Helpfulness", "C"]
	X_stage1 = df[stage1_features]

	scaler1 = MinMaxScaler()
	X_stage1_scaled = scaler1.fit_transform(X_stage1)

	kmeans_stage1 = KMeans(n_clusters=2, random_state=42, n_init=10)
	df["Stage1_Cluster"] = kmeans_stage1.fit_predict(X_stage1_scaled)

	cluster1_profiles = df.groupby("Stage1_Cluster")["Helpfulness"].mean()
	expert_cluster_id = cluster1_profiles.idxmax()
	non_expert_cluster_id = cluster1_profiles.idxmin()

	my_single_model.scaler1 = scaler1
	my_single_model.kmeans1 = kmeans_stage1
	my_single_model.expert_cluster_id = int(expert_cluster_id)
	my_single_model.non_expert_cluster_id = int(non_expert_cluster_id)

	df_nhom1 = df[df["Stage1_Cluster"] == expert_cluster_id].copy()
	df_tang2_input = df[df["Stage1_Cluster"] == non_expert_cluster_id].copy()

	df_nhom1["Final_Cluster_Label"] = "Nhóm 1: Chuyên gia đánh giá"
	print(f"  -> Da tach xong Nhom 1: {len(df_nhom1)} dong.")

	# ============================================================
	# 2) TANG 2: Tach Toxic vs Qua duong
	# ============================================================
	print("\n[TANG 2] Dang phan tach nhóm khách hàng có tiêu chuẩn cao, khách hàng có tâm lý thoải mái")

	stage2_features = ["Tiêu_cực", "Tích_cực", "N"]
	X_stage2 = df_tang2_input[stage2_features]

	scaler2 = MinMaxScaler()
	X_stage2_scaled = scaler2.fit_transform(X_stage2)

	kmeans_stage2 = KMeans(n_clusters=2, random_state=42, n_init=10)
	df_tang2_input["Stage2_Cluster"] = kmeans_stage2.fit_predict(X_stage2_scaled)

	cluster2_profiles = df_tang2_input.groupby("Stage2_Cluster")["Tiêu_cực"].mean()
	toxic_cluster_id = cluster2_profiles.idxmax()
	casual_cluster_id = cluster2_profiles.idxmin()

	my_single_model.scaler2 = scaler2
	my_single_model.kmeans2 = kmeans_stage2
	my_single_model.toxic_cluster_id = int(toxic_cluster_id)
	my_single_model.casual_cluster_id = int(casual_cluster_id)

	df_tang2_input["Final_Cluster_Label"] = np.where(
		df_tang2_input["Stage2_Cluster"] == toxic_cluster_id,
		"Nhóm 2: Khách hàng có tiêu chuẩn cao",
		"Nhóm 3: Khách hàng có tâm lý thoải mái",
	)

	toxic_count = int((df_tang2_input["Stage2_Cluster"] == toxic_cluster_id).sum())
	casual_count = int((df_tang2_input["Stage2_Cluster"] == casual_cluster_id).sum())
	print(f"  -> Da tach xong Tang 2: Nhom 2 ({toxic_count}) | Nhom 3 ({casual_count}).")

	# ============================================================
	# 3) Tong hop ket qua
	# ============================================================
	df_final = pd.concat([df_nhom1, df_tang2_input], axis=0).sort_index()

	print("\n" + "=" * 20 + " BAO CAO SO LUONG PHAN BO " + "=" * 20)
	print(df_final["Final_Cluster_Label"].value_counts())
	print("=" * 70 + "\n")

	all_features = ["O", "C", "E", "A", "N", "Helpfulness", "Tiêu_cực", "Trung_tính", "Tích_cực"]
	final_report = df_final.groupby("Final_Cluster_Label")[all_features].mean()

	print("BANG THONG SO TRUNG BINH CUA MO HINH PHAN TANG")
	print(final_report.round(3))
	print("-" * 70 + "\n")

	# ============================================================
	# 4) Danh gia chat luong phan cum
	# ============================================================
	X_eval = df_final[all_features].values
	labels_eval = df_final["Final_Cluster_Label"].values

	sil_avg = silhouette_score(X_eval, labels_eval)
	db_index = davies_bouldin_score(X_eval, labels_eval)
	ch_index = calinski_harabasz_score(X_eval, labels_eval)

	print("DO DO TOAN HOC CHAT LUONG PHAN CUM TOAN CUC")
	print(f"- Silhouette Score: {sil_avg:.4f}")
	print(f"- Davies-Bouldin Index: {db_index:.4f}")
	print(f"- Calinski-Harabasz Index: {ch_index:.2f}\n")

	X_eval_stage1 = df[stage1_features].values
	labels_eval_stage1 = df["Stage1_Cluster"].values
	sil_s1 = silhouette_score(X_eval_stage1, labels_eval_stage1)
	db_s1 = davies_bouldin_score(X_eval_stage1, labels_eval_stage1)
	ch_s1 = calinski_harabasz_score(X_eval_stage1, labels_eval_stage1)

	X_eval_stage2 = df_tang2_input[stage2_features].values
	labels_eval_stage2 = df_tang2_input["Stage2_Cluster"].values
	sil_s2 = silhouette_score(X_eval_stage2, labels_eval_stage2)
	db_s2 = davies_bouldin_score(X_eval_stage2, labels_eval_stage2)
	ch_s2 = calinski_harabasz_score(X_eval_stage2, labels_eval_stage2)

	print("DO DO NOI TAI THEO TUNG TANG")
	print(f"- Tang 1 | Silhouette: {sil_s1:.4f} | DB: {db_s1:.4f} | CH: {ch_s1:.2f}")
	print(f"- Tang 2 | Silhouette: {sil_s2:.4f} | DB: {db_s2:.4f} | CH: {ch_s2:.2f}\n")

	print("KIEM DINH ANOVA THEO DAC TRUNG")
	unique_labels = df_final["Final_Cluster_Label"].unique()
	for col in all_features:
		groups = [df_final[df_final["Final_Cluster_Label"] == label][col].values for label in unique_labels]
		f_stat, p_val = stats.f_oneway(*groups)
		print(f"- {col:<11}: F = {f_stat:<8.2f} | p = {p_val:<10.4e}")

	# ============================================================
	# 5) Truc quan hoa (PCA + t-SNE)
	# ============================================================
	print("\nDang truc quan hoa khong gian phan cum (PCA & t-SNE)...")

	scaler_visual = StandardScaler()
	X_visual_scaled = scaler_visual.fit_transform(X_eval)

	cluster_colors = {
		"Nhóm 1: Chuyên gia đánh giá": "#2ecc71",
		"Nhóm 2: Toxic / Khó tính": "#e74c3c",
		"Nhóm 3: Người qua đường dễ dãi": "#3498db",
	}

	plt.rcParams["font.family"] = "sans-serif"
	fig, axes = plt.subplots(1, 2, figsize=(20, 8))

	print(">> Dang chay PCA...")
	pca = PCA(n_components=2, random_state=42)
	X_pca = pca.fit_transform(X_visual_scaled)
	var_exp = pca.explained_variance_ratio_ * 100

	df_pca = pd.DataFrame(X_pca, columns=["PC1", "PC2"])
	df_pca["Cluster"] = labels_eval

	sns.scatterplot(
		ax=axes[0],
		data=df_pca,
		x="PC1",
		y="PC2",
		hue="Cluster",
		palette=cluster_colors,
		alpha=0.6,
		s=50,
		edgecolor="w",
		linewidth=0.3,
	)
	axes[0].set_title(
		f"A. Khong gian phan cum qua PCA\\n(Tong phuong sai giai thich: {var_exp[0] + var_exp[1]:.2f}%)",
		fontsize=13,
		fontweight="bold",
		pad=15,
	)
	axes[0].set_xlabel(f"Principal Component 1 ({var_exp[0]:.2f}%)", fontsize=11)
	axes[0].set_ylabel(f"Principal Component 2 ({var_exp[1]:.2f}%)", fontsize=11)
	axes[0].grid(True, linestyle="--", alpha=0.5)
	axes[0].legend(title="Phan khuc khach hang", loc="upper right", frameon=True, facecolor="white")

	print(">> Dang chay t-SNE...")
	tsne = TSNE(n_components=2, perplexity=30, n_iter=1000, random_state=42)
	X_tsne = tsne.fit_transform(X_visual_scaled)

	df_tsne = pd.DataFrame(X_tsne, columns=["t-SNE 1", "t-SNE 2"])
	df_tsne["Cluster"] = labels_eval

	sns.scatterplot(
		ax=axes[1],
		data=df_tsne,
		x="t-SNE 1",
		y="t-SNE 2",
		hue="Cluster",
		palette=cluster_colors,
		alpha=0.6,
		s=50,
		edgecolor="w",
		linewidth=0.3,
	)
	axes[1].set_title("B. Khong gian cau truc mat do qua t-SNE", fontsize=13, fontweight="bold", pad=15)
	axes[1].set_xlabel("t-SNE Dimension 1", fontsize=11)
	axes[1].set_ylabel("t-SNE Dimension 2", fontsize=11)
	axes[1].grid(True, linestyle="--", alpha=0.5)
	axes[1].legend(title="Phan khuc khach hang", loc="upper right", frameon=True, facecolor="white")

	plt.tight_layout()
	output_fig_path = os.path.join(root, "src", "clustering", "hierarchical_clustering_output.png")
	plt.savefig(output_fig_path, dpi=300, bbox_inches="tight")
	print(f"Da ket xuat do thi tai: {output_fig_path}")
	plt.show()

	# Drop nhan phu truoc khi xuat file ket qua
	df_final = df_final.drop(columns=["Stage1_Cluster", "Stage2_Cluster"], errors="ignore")

	output_file = os.path.join(root, "src", "clustering", "clustering_2stages_results.csv")
	df_final.to_csv(output_file, index=False, encoding="utf-8-sig")

	model_output_path = os.path.join(root, "src", "clustering", "hierarchical_clustering_model.pkl")
	joblib.dump(my_single_model, model_output_path)

	print("\nHE THONG PHAN TANG DA CHAY XONG")
	print(f"- File du lieu da gan nhan: {output_file}")
	print(f"- File model: {model_output_path}")


if __name__ == "__main__":
	main()
	print("a");
