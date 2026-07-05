import axios from "axios";

const baseURL = process.env.NEXT_PUBLIC_API_URL || (
  typeof window === "undefined"
    ? "http://backend:8000/api/v1"
    : "/api/v1"
);

// Configure the global raw axios singleton base URL to prevent broken relative URLs on external static hosts like Vercel
let rawBaseURL = baseURL;
if (rawBaseURL.endsWith("/api/v1")) {
  rawBaseURL = rawBaseURL.slice(0, -7);
} else if (rawBaseURL.endsWith("/api/v1/")) {
  rawBaseURL = rawBaseURL.slice(0, -8);
}
axios.defaults.baseURL = rawBaseURL;

const axiosInstance = axios.create({
  baseURL,
  withCredentials: true, // critical to send refresh token cookie
  headers: {
    "Content-Type": "application/json",
  },
});

// Interceptor to inject Bearer access token
axiosInstance.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor to handle automatic 401 token refresh loops
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(error);
    }
  });
  failedQueue = [];
};

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is 401 and request wasn't already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      // If we are already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return axiosInstance(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        // Hitting refresh token endpoint (sends httpOnly cookie automatically)
        const response = await axios.post(
          `${baseURL}/auth/refresh`,
          {},
          { withCredentials: true }
        );
        
        const newAccessToken = response.data.access_token;
        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", newAccessToken);
        }
        
        axiosInstance.defaults.headers.common["Authorization"] = `Bearer ${newAccessToken}`;
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        
        processQueue(null, newAccessToken);
        isRefreshing = false;
        
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        
        // Log out user & clear session
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("user_info");
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default axiosInstance;
