import api from "../api";

export const getUserList = async ({ page = 0, size = 5, keyword } = {}) => {
    const params = {
        page,
        size,
    };

    if (keyword != null && String(keyword).trim() !== "") {
        params.keyword = String(keyword).trim();
    }

    const response = await api.get("/admin/users", { params });
    return response.data.result;
};
export const getDashboard = async () => {
    const response = await api.get("/admin/dashboard");

    return response.data.result;
};
export const getSentiment = async () => {
    const response = await api.get("/admin/statistics/sentiment");

    return response.data.result;
};
export const getBigFive = async () => {
    const response = await api.get("/admin/statistics/personality");

    return response.data.result;
};
export const getReviewsByDate = async () => {
    const response = await api.get("/admin/statistics/reviews-by-date");

    return response.data.result;
};
export const getDetailUser = async (id) => {

    const response = await api.get(`/admin/user/detail/${id}`);

    return response.data.result;
};
export const getReviewDetail = async (reviewId) => {
    const response = await api.get(
        `/admin/reviews/${reviewId}`
    );

    return response.data.result;
};

export const getAllReviews = async ({ page = 0, size = 5 } = {}) => {
    const response = await api.get("/admin/reviews", {
        params: { page, size },
    });

    return response.data.result;
};
export const lockCustomer = async (userId) => {
  const res = await api.put("/admin/lock", null, {
    params: {
      userId: userId,
    },
  });
  return res.data.result;
};
export const unlockCustomer = async (userId) => {
  const res = await api.put("/admin/unlock", null, {
    params: {
      userId: userId,
    },
  });
  return res.data.result;
};