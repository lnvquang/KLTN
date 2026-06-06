import api from "../api";

export const analyzeReview = async (text) => {
    const response = await api.post("/reviews/analyze", {
        text,
    });

    return response.data.result;
};
export const getHistoryReview = async () => {
    const response = await api.get("/reviews/history"
    );

    return response.data.result;
};
export const getDetailReview = async (id) => {
    const response = await api.get("/reviews/history/detail", {
        params: {
            id,
        },
    });

    return response.data.result;
};