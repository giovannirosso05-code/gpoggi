import { renderHeader, renderFooter } from "./common.js";
renderHeader(location.pathname.includes("chi-siamo") ? "chi-siamo" : "");
renderFooter();
