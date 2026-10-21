import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  ChartNoAxesCombined,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Download,
  Eraser,
  Flag,
  FolderOpen,
  Highlighter,
  HelpCircle,
  History,
  Keyboard,
  LayoutGrid,
  Leaf,
  LoaderCircle,
  Maximize2,
  MoreHorizontal,
  Pause,
  Play,
  RotateCcw,
  Search,
  Settings2,
  ShieldCheck,
  StickyNote,
  Upload,
  WifiOff,
  X,
} from "lucide-react";
import { api, post } from "./api";
import type {
  Annotation,
  Attempt,
  Group,
  Library,
  Option,
  Passage,
  Result,
  SourceImage,
  TestCard,
} from "./types";
import { typeNames } from "./types";
import { useAttempt } from "./useAttempt";
import { Annotated } from "./Annotated";
import { highlightSelection } from "./annotations";
import {
  InteractiveTable,
  MatchingMatrix,
  answerPartsFor,
} from "./QuestionLayouts";
import type { TextRange } from "./types";
import "./style.css";
import "./inline.css";
import "./exam-upgrade.css";
import "./listening.css";
import "./experience.css";
import { Modal } from "./Dialog";
import { ExamNavigation } from "./ExamNavigation";
import {
  DisplaySettings,
  ExamHelp,
  StartOrientation,
  useExamPreferences,
  onTabKeyDown,
  FAMILIARISATION_KEY,
} from "./ExamSupport";
import { Familiarisation } from "./Familiarisation";
import { ListeningMatching } from "./ListeningMatching";
import { ExtendedLayout } from "./ListeningLayouts";
import {
  ListeningPlayer,
  ListeningStartModal,
  clockText,
  listeningRemaining,
} from "./ListeningPlayer";

const date = (n: number) =>
  new Date(n * 1000).toLocaleString("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "Asia/Ho_Chi_Minh",
  });
const answered = (a: Attempt) =>
  a.numbers.filter((n) => a.answers[n]?.trim()).length;
const visibleUnits = (a: Attempt) =>
  a.test.passages.filter((p) =>
    a.skill === "listening"
      ? !a.part || p.number === a.part
      : a.mode === "exam" || p.number === a.passage
  );
const statusName: Record<string, string> = {
  active: "Đang làm",
  paused: "Tạm dừng",
  submitted: "Chưa chấm",
  graded: "Đã chấm",
};
function Brand() {
  return (
    <div className="brand">
      <span className="brand-symbol">
        <BookOpen size={22} />
      </span>
      <span>
        Tu Luyện<span className="brand-light">IELTS</span>
        <small>ĐỘT PHÁ TU VI</small>
      </span>
    </div>
  );
}
function SourceViewer({
  images,
  onClose,
}: {
  images: SourceImage[];
  onClose: () => void;
}) {
  return (
    <Modal title="Đối chiếu tài liệu gốc" onClose={onClose} wide>
      <p className="muted">
        Trang nguồn được lưu ngay trên máy. Số trang dưới đây là số trang trong
        PDF.
      </p>
      <div className="source-images">
        {images.map((s, i) => (
          <figure key={i}>
            <figcaption>Trang PDF {s.page}</figcaption>
            <img
              src={s.url}
              alt={"Tài liệu gốc, trang " + s.page}
              loading="lazy"
            />
          </figure>
        ))}
      </div>
    </Modal>
  );
}

function App() {
  const [skill, setSkill] = useState<"reading" | "listening">(() =>
    localStorage.getItem("reading-room:skill") === "listening"
      ? "listening"
      : "reading"
  );
  useEffect(() => localStorage.setItem("reading-room:skill", skill), [skill]);
  const skillName = skill === "listening" ? "Listening" : "Reading";
  let guideDone = false;
  try {
    guideDone = localStorage.getItem(FAMILIARISATION_KEY) === "completed";
  } catch {}
  const [route, setRoute] = useState(location.hash.slice(1) || "/");
  const [library, setLibrary] = useState<Library | null>(null),
    [attempts, setAttempts] = useState<Attempt[]>([]);
  const [error, setError] = useState(""),
    [book, setBook] = useState(() => {
      try {
        const n = Number(localStorage.getItem("reading-room:book"));
        return Number.isInteger(n) && n >= 13 && n <= 20 ? n : 20;
      } catch {
        return 20;
      }
    }),
    [start, setStart] = useState<TestCard | null>(null);
  useEffect(() => {
    try {
      localStorage.setItem("reading-room:book", String(book));
    } catch {}
  }, [book]);
  const refreshSequence = useRef(0);
  const navigate = (path: string) => {
    location.hash = path;
  };
  const refresh = useCallback(async () => {
    const sequence = ++refreshSequence.current;
    try {
      const [l, a] = await Promise.all([
        api<Library>("/library?skill=" + skill),
        api<Attempt[]>("/attempts?skill=" + skill),
      ]);
      if (sequence !== refreshSequence.current) return;
      setLibrary(l);
      setAttempts(a);
      setError("");
    } catch (e) {
      if (sequence === refreshSequence.current) setError((e as Error).message);
    }
  }, [skill]);
  useEffect(() => {
    const h = () => setRoute(location.hash.slice(1) || "/");
    addEventListener("hashchange", h);
    void refresh();
    const t = setInterval(refresh, 30000);
    return () => {
      removeEventListener("hashchange", h);
      clearInterval(t);
    };
  }, [refresh]);
  useEffect(() => {
    if (!route.startsWith("/attempt/")) void refresh();
  }, [route, refresh]);
  if (route === "/familiarisation")
    return <Familiarisation onBack={() => navigate("/")} />;
  if (route.startsWith("/attempt/"))
    return (
      <Exam
        key={route.split("/")[2]}
        id={route.split("/")[2]}
        onBack={() => navigate("/")}
      />
    );
  const current = attempts.find((a) => ["active", "paused"].includes(a.status));
  const graded = attempts.filter((a) => a.result);
  const totalCorrect = graded.reduce((s, a) => s + a.result!.score, 0),
    totalMarked = graded.reduce((s, a) => s + a.result!.total, 0);
  const selected = library?.books.find((b) => b.number === book);
  const panel =
    route === "/history"
      ? "history"
      : route === "/stats"
      ? "stats"
      : route === "/settings"
      ? "settings"
      : "library";
  return (
    <div className="workspace">
      <aside className="sidebar">
        <Brand />
        <div className="sidebar-label">KHÔNG GIAN HỌC TẬP</div>
        <nav>
          {[
            { id: "library", path: "/", name: "Thư viện đề", icon: LayoutGrid },
            {
              id: "familiarisation",
              path: "/familiarisation",
              name: "Làm quen giao diện",
              icon: Keyboard,
            },
            {
              id: "history",
              path: "/history",
              name: "Lịch sử làm bài",
              icon: History,
            },
            {
              id: "stats",
              path: "/stats",
              name: "Tiến độ học tập",
              icon: ChartNoAxesCombined,
            },
          ].map((n) => (
            <button
              className={panel === n.id ? "nav-item active" : "nav-item"}
              key={n.id}
              onClick={() => navigate(n.path)}
            >
              <n.icon size={19} />
              {n.name}
              {n.id === "library" && (
                <span className="nav-count">{library?.readyCount || 0}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="quiet-card">
            <Leaf size={22} />
            <strong>
              {skill === "listening"
                ? "Lắng nghe mỗi ngày."
                : "Một bài đọc mỗi ngày."}
            </strong>
            <p>Dành một khoảng thời gian nhỏ để tạo nên sự tiến bộ lớn.</p>
          </div>
          <button
            className={"nav-item " + (panel === "settings" ? "active" : "")}
            onClick={() => navigate("/settings")}
          >
            <Settings2 size={18} />
            Cài đặt & sao lưu
          </button>
          <div className="local-status">
            <span />
            Dữ liệu lưu trên máy của bạn
            <small>Không gian riêng · Hoàn toàn offline</small>
          </div>
        </div>
      </aside>
      <div className="workspace-main">
        <header className="workspace-top">
          <span>
            IELTS Academic <ChevronRight size={14} />
            <strong>{skillName}</strong>
          </span>
          <span className="offline-pill">
            <ShieldCheck size={14} />
            Local workspace
          </span>
        </header>
        <main className="dashboard">
          <div className="skill-switch" role="group" aria-label="Kỹ năng IELTS">
            {(["reading", "listening"] as const).map((k) => (
              <button
                key={k}
                aria-pressed={skill === k}
                className={skill === k ? "selected" : ""}
                onClick={() => {
                  if (k === skill) return;
                  refreshSequence.current++;
                  setLibrary(null);
                  setAttempts([]);
                  setSkill(k);
                }}
              >
                {k === "reading" ? "Reading" : "Listening"}
              </button>
            ))}
          </div>
          {error && (
            <div className="alert">
              {error}
              <button onClick={refresh}>Thử lại</button>
            </div>
          )}
          {panel === "library" && (
            <>
              <div className="page-title">
                <div>
                  <div className="eyebrow">LUYỆN TẬP THEO NHỊP CỦA BẠN</div>
                  <h1>
                    Không gian luyện {skillName} của bạn<span>.</span>
                  </h1>
                  <p>
                    Đề Cambridge quen thuộc. Trải nghiệm thi thật. Theo nhịp học
                    của bạn.
                  </p>
                </div>
                <div className="title-icon">
                  <BookOpen size={32} />
                </div>
              </div>
              {current && (
                <section className="hero library-hero">
                  <div className="hero-copy">
                    <div className="hero-kicker">
                      <span /> LUYỆN TẬP CÓ CHỦ ĐÍCH
                    </div>
                    <h2>
                      {current
                        ? "Bài làm đang chờ bạn tiếp tục."
                        : skill === "listening"
                        ? "Lắng nghe. Hiểu thêm từng ngày."
                        : "Một khoảng lặng. Một bài đọc mới."}
                    </h2>
                    <p>
                      {current
                        ? `${current.title}${
                            current.passage
                              ? " · Passage " + current.passage
                              : ""
                          } · Đã trả lời ${answered(current)}/${
                            current.numbers.length
                          } câu`
                        : `Chọn một đề bên dưới và bắt đầu luyện ${skillName}. Mọi tiến bộ được lưu ngay trên máy của bạn.`}
                    </p>
                    <button
                      className="button light"
                      onClick={() =>
                        current
                          ? navigate("/attempt/" + current.id)
                          : document
                              .getElementById("test-library")
                              ?.scrollIntoView({ behavior: "smooth" })
                      }
                    >
                      {current ? "Tiếp tục làm bài" : "Khám phá thư viện"}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                  <div className="hero-art" aria-hidden="true">
                    <div className="art-orbit" />
                    <div className="art-page back" />
                    <div className="art-page front">
                      <BookOpen size={30} />
                      <i />
                      <i />
                      <i />
                      <i className="short" />
                      <span>
                        <Check size={14} /> YOUR NEXT CHAPTER
                      </span>
                    </div>
                    <div className="art-leaf">
                      <Leaf size={27} />
                    </div>
                  </div>
                </section>
              )}
              <div className="familiarisation-invite">
                <span className="invite-icon">
                  <Keyboard size={25} />
                </span>
                <div>
                  <span className="invite-eyebrow">TRƯỚC KHI BẮT ĐẦU</span>
                  <h2>
                    {guideDone
                      ? "Bạn đã sẵn sàng với giao diện thi."
                      : "Làm quen trước. Tự tin khi thi."}
                  </h2>
                  <p>
                    Thử điền đáp án, cắm cờ, highlight và điều hướng trên chính
                    giao diện làm bài.
                  </p>
                </div>
                <button
                  className="button secondary"
                  onClick={() => navigate("/familiarisation")}
                >
                  {guideDone ? "Thử lại thao tác" : "Làm quen giao diện"}
                  <ArrowRight size={17} />
                </button>
              </div>
              <div className="stat-grid library-stats">
                <Stat
                  icon={<FolderOpen size={20} />}
                  value={library?.readyCount || 0}
                  label="Đề sẵn sàng luyện tập"
                  detail="Cambridge 13–20"
                />
                <Stat
                  icon={<CheckCircle2 size={20} />}
                  value={graded.length}
                  label="Lượt đã hoàn thành"
                  detail="Mỗi lần luyện đều được lưu lại"
                />
                <Stat
                  icon={<ChartNoAxesCombined size={20} />}
                  value={
                    totalMarked
                      ? Math.round((totalCorrect / totalMarked) * 100) + "%"
                      : "—"
                  }
                  label="Tỷ lệ trả lời đúng"
                  detail={
                    totalMarked
                      ? `${totalCorrect}/${totalMarked} câu đã chấm`
                      : "Bắt đầu một đề để xem tiến độ"
                  }
                />
              </div>
              <section id="test-library" className="library-section">
                <div className="section-heading">
                  <div>
                    <h2>Thư viện Cambridge</h2>
                    <p>Chọn bộ sách và bắt đầu bài luyện phù hợp.</p>
                  </div>
                  <span className="subtle-tag">{skillName.toUpperCase()}</span>
                </div>
                <div
                  className="book-tabs"
                  role="tablist"
                  aria-label="Sách Cambridge"
                  onKeyDown={onTabKeyDown}
                >
                  {library?.books.map((b) => (
                    <button
                      key={b.number}
                      role="tab"
                      aria-selected={book === b.number}
                      className={book === b.number ? "selected" : ""}
                      onClick={() => setBook(b.number)}
                    >
                      <span>Cambridge</span>
                      <strong>{b.number}</strong>
                      {!b.available && <small>Chưa có</small>}
                    </button>
                  ))}
                </div>
                {!library ? (
                  <div className="empty">
                    <LoaderCircle className="spin" />
                    Đang mở thư viện…
                  </div>
                ) : !selected?.available ? (
                  <div className="empty">
                    <BookOpen size={35} />
                    <h3>Cambridge {book} đang được chuẩn bị</h3>
                    <p>
                      Bổ sung PDF rồi chạy công cụ chuẩn bị thư viện để thêm bộ
                      đề này.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="collection-label">
                      <strong>Cambridge IELTS {book}</strong>
                      <span>
                        {skill === "listening"
                          ? "4 đề · 16 Parts · 160 câu hỏi"
                          : "4 đề · 12 bài đọc · 160 câu hỏi"}
                      </span>
                    </div>
                    <div className="test-grid">
                      {selected.tests.map((t) => {
                        const history = attempts.filter(
                            (a) => a.testId === t.id
                          ),
                          last = history[0],
                          unfinished = history.find((a) =>
                            ["active", "paused"].includes(a.status)
                          );
                        return (
                          <article className="test-card" key={t.id}>
                            <div className="test-card-top">
                              <span className="test-number">
                                TEST {String(t.test).padStart(2, "0")}
                              </span>
                              <span
                                className={
                                  "ready-badge " + (t.ready ? "" : "waiting")
                                }
                              >
                                {t.ready ? (
                                  <>
                                    <span />
                                    Sẵn sàng
                                  </>
                                ) : (
                                  <>Đang đối chiếu</>
                                )}
                              </span>
                            </div>
                            <h3>
                              {skill === "listening"
                                ? "Listening"
                                : "Academic Reading"}
                            </h3>
                            <div className="test-meta">
                              <span>
                                <Clock3 size={14} />
                                {skill === "listening"
                                  ? "Theo audio"
                                  : "60 phút"}
                              </span>
                              <span>40 câu hỏi</span>
                              <span>
                                {skill === "listening"
                                  ? "4 Parts"
                                  : "3 passages"}
                              </span>
                            </div>
                            <div className="passage-preview">
                              {t.passages.length ? (
                                t.passages.map((p) => (
                                  <div key={p.number}>
                                    <span>{p.number}</span>
                                    <p title={p.title}>{p.title}</p>
                                  </div>
                                ))
                              ) : (
                                <p className="muted">
                                  Đang số hoá bài đọc và kiểm tra đáp án từ tài
                                  liệu của bạn.
                                </p>
                              )}
                            </div>
                            <div className="test-card-bottom">
                              <span>
                                {history.length
                                  ? `${history.length} lượt làm bài`
                                  : "Chưa làm bài"}
                                {last?.result && (
                                  <small>
                                    Gần nhất{" "}
                                    <strong>
                                      {last.result.score}/{last.result.total}
                                    </strong>
                                  </small>
                                )}
                                {unfinished && (
                                  <button
                                    className="text-button resume-card"
                                    onClick={() =>
                                      navigate("/attempt/" + unfinished.id)
                                    }
                                  >
                                    Tiếp tục bài đang dở{" "}
                                    <ArrowRight size={11} />
                                  </button>
                                )}
                              </span>
                              <button
                                className="button small"
                                disabled={!t.ready}
                                onClick={() => setStart(t)}
                              >
                                Làm bài
                                <ArrowRight size={15} />
                              </button>
                            </div>
                          </article>
                        );
                      })}
                    </div>
                  </>
                )}
              </section>
              <div className="library-footnote">
                <ShieldCheck size={16} />
                <span>
                  Đề, đáp án và lịch sử ở lại trên máy của bạn. Bạn có thể học
                  ngay cả khi không có Internet.
                </span>
              </div>
            </>
          )}
          {panel === "history" && (
            <>
              <PageTitle
                eyebrow="NHÌN LẠI ĐỂ TIẾN BỘ"
                title="Lịch sử làm bài"
                text="Đáp án, ghi chú và những lần cố gắng của bạn được giữ nguyên tại đây."
              />
              {attempts.length ? (
                <div className="history-table">
                  <div className="history-header">
                    <span>Đề / Chế độ</span>
                    <span>Thời gian bắt đầu</span>
                    <span>Trạng thái</span>
                    <span>Kết quả</span>
                    <span />
                  </div>
                  {attempts.map((a) => (
                    <button
                      className="history-row"
                      key={a.id}
                      onClick={() => navigate("/attempt/" + a.id)}
                    >
                      <div>
                        <strong>{a.title}</strong>
                        <small>
                          {a.skill === "listening"
                            ? a.mode === "exam"
                              ? "Thi sát thật"
                              : a.part
                              ? "Luyện Part " + a.part
                              : "Luyện cả đề"
                            : a.mode === "exam"
                            ? "Thi thử đủ đề"
                            : `Luyện Passage ${a.passage}`}
                        </small>
                      </div>
                      <span>{date(a.startedAt)}</span>
                      <span className={"status-pill " + a.status}>
                        {statusName[a.status]}
                      </span>
                      <strong>
                        {a.result
                          ? `${a.result.score}/${a.result.total}${
                              a.result.band !== null
                                ? " · Band " + a.result.band
                                : ""
                            }`
                          : `${answered(a)}/${a.numbers.length} câu`}
                      </strong>
                      <ChevronRight size={18} />
                    </button>
                  ))}
                </div>
              ) : (
                <Empty
                  title="Trang đầu tiên vẫn đang chờ"
                  text={`Làm một bài ${skillName}, lịch sử của bạn sẽ xuất hiện ở đây.`}
                />
              )}
            </>
          )}
          {panel === "stats" && (
            <>
              <PageTitle
                eyebrow="HIỂU CÁCH MÌNH HỌC"
                title="Tiến độ học tập"
                text="Thống kê từ các lượt đã chấm, bao gồm cả những lần làm lại."
              />
              <div className="stat-grid">
                <Stat
                  icon={<CheckCircle2 size={20} />}
                  value={graded.length}
                  label="Lượt đã chấm"
                  detail="Thi thử và luyện từng phần"
                />
                <Stat
                  icon={<BookOpen size={20} />}
                  value={totalCorrect}
                  label="Câu trả lời đúng"
                  detail={`Trên ${totalMarked} câu đã chấm`}
                />
                <Stat
                  icon={<ChartNoAxesCombined size={20} />}
                  value={
                    totalMarked
                      ? Math.round((totalCorrect / totalMarked) * 100) + "%"
                      : "—"
                  }
                  label="Độ chính xác tổng thể"
                  detail="Theo toàn bộ lịch sử"
                />
              </div>
              <div className="content-panel">
                <h2>Độ chính xác theo dạng câu hỏi</h2>
                {totalMarked ? (
                  <TypeBreakdown results={graded.map((a) => a.result!)} />
                ) : (
                  <p className="muted">
                    Hoàn thành và chấm bài đầu tiên để biết dạng câu hỏi cần
                    luyện thêm.
                  </p>
                )}
              </div>
              <div className="content-panel">
                <h2>Những lượt làm gần đây</h2>
                {graded.slice(0, 8).map((a) => (
                  <div className="recent-score" key={a.id}>
                    <span>
                      {a.title}
                      <small>{date(a.startedAt)}</small>
                    </span>
                    <div className="progress-track">
                      <i
                        style={{
                          width:
                            (a.result!.score / a.result!.total) * 100 + "%",
                        }}
                      />
                    </div>
                    <strong>
                      {a.result!.score}/{a.result!.total}
                    </strong>
                  </div>
                ))}
                {!graded.length && <p className="muted">Chưa có kết quả.</p>}
              </div>
            </>
          )}
          {panel === "settings" && <Settings refresh={refresh} />}
        </main>
        <footer className="workspace-footer">
          <span>readingroom · Không gian tự học của bạn</span>
          <span>{skillName.toUpperCase()} / LOCAL EDITION</span>
        </footer>
      </div>
      {start &&
        (start.skill === "listening" ? (
          <ListeningStartModal
            test={start}
            onClose={() => setStart(null)}
            onFamiliarise={() => {
              setStart(null);
              navigate("/familiarisation");
            }}
            onStart={(a) => {
              setStart(null);
              navigate("/attempt/" + a.id);
            }}
          />
        ) : (
          <StartModal
            test={start}
            onClose={() => setStart(null)}
            onFamiliarise={() => {
              setStart(null);
              navigate("/familiarisation");
            }}
            onStart={(a) => {
              setStart(null);
              navigate("/attempt/" + a.id);
            }}
          />
        ))}
    </div>
  );
}
function PageTitle({
  eyebrow,
  title,
  text,
}: {
  eyebrow: string;
  title: string;
  text: string;
}) {
  return (
    <div className="page-title">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>
          {title}
          <span>.</span>
        </h1>
        <p>{text}</p>
      </div>
    </div>
  );
}
function Stat({
  icon,
  value,
  label,
  detail,
}: {
  icon: React.ReactNode;
  value: React.ReactNode;
  label: string;
  detail: string;
}) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div>
        <strong className="stat-value">{value}</strong>
        <span className="stat-label">{label}</span>
        <small>{detail}</small>
      </div>
    </div>
  );
}
function Empty({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty">
      <BookOpen size={34} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}
function TypeBreakdown({ results }: { results: Result[] }) {
  const groups: Record<string, { correct: number; total: number }> = {};
  results.forEach((r) =>
    Object.entries(r.byType).forEach(([k, v]) => {
      groups[k] ??= { correct: 0, total: 0 };
      groups[k].correct += v.correct;
      groups[k].total += v.total;
    })
  );
  return (
    <div className="type-breakdown">
      {Object.entries(groups).map(([k, v]) => (
        <div key={k}>
          <div>
            <span>{typeNames[k] || k}</span>
            <strong>
              {v.correct}/{v.total}{" "}
              <small>· {Math.round((v.correct / v.total) * 100)}%</small>
            </strong>
          </div>
          <div className="progress-track">
            <i style={{ width: (v.correct / v.total) * 100 + "%" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
function StartModal({
  test,
  onClose,
  onStart,
  onFamiliarise,
}: {
  test: TestCard;
  onClose: () => void;
  onStart: (a: Attempt) => void;
  onFamiliarise: () => void;
}) {
  const [examTiming, setExamTiming] = useState<"timed" | "untimed">("timed");
  const [mode, setMode] = useState("exam"),
    [passage, setPassage] = useState(1),
    [minutes, setMinutes] = useState(20),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const begin = async () => {
    setBusy(true);
    try {
      onStart(
        await post<Attempt>("/attempts", {
          testId: test.id,
          mode,
          passage,
          minutes,
          examTiming,
        })
      );
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  };
  return (
    <Modal
      title={`Cambridge ${test.book} · Test ${test.test}`}
      onClose={onClose}
    >
      <p className="muted">
        Chọn cách làm bài. Đồng hồ chỉ bắt đầu khi bạn bấm nút bắt đầu bên dưới.
      </p>
      <StartOrientation onOpen={onFamiliarise} />
      <div className="mode-options">
        <button
          className={mode === "exam" ? "mode selected" : "mode"}
          aria-pressed={mode === "exam"}
          onClick={() => setMode("exam")}
        >
          <Clock3 />
          <strong>Thi thử</strong>
          <small>40 câu · 3 passages</small>
        </button>
        <button
          className={mode === "practice" ? "mode selected" : "mode"}
          aria-pressed={mode === "practice"}
          onClick={() => setMode("practice")}
        >
          <BookOpen />
          <strong>Luyện passage</strong>
          <small>Chủ động thời gian</small>
        </button>
      </div>
      {mode === "exam" ? (
        <>
          <fieldset className="exam-timing-choice">
            <legend>Thời gian thi thử</legend>
            <label>
              <input
                type="radio"
                name="exam-timing"
                checked={examTiming === "timed"}
                onChange={() => setExamTiming("timed")}
              />
              60 phút
            </label>
            <label>
              <input
                type="radio"
                name="exam-timing"
                checked={examTiming === "untimed"}
                onChange={() => setExamTiming("untimed")}
              />
              Không giới hạn
            </label>
          </fieldset>
          <div className="info-box">
            <strong>
              {examTiming === "timed"
                ? "Một phiên thi trọn vẹn"
                : "Luyện trọn đề theo nhịp của bạn"}
            </strong>
            <p>
              {examTiming === "timed"
                ? "Đồng hồ chạy liên tục, kể cả khi bạn đóng tab. Hết giờ tự nộp bài. Bạn có thể chuyển sang không hạn giờ khi bài còn đang làm."
                : "Đồng hồ đếm thời gian đã làm. Có thể Pause để nghỉ và che nội dung. Đóng tab không tự dừng thời gian; bạn chủ động nộp bài khi xong."}
            </p>
          </div>
        </>
      ) : (
        <div className="practice-options">
          <label>
            Bài đọc
            <select
              value={passage}
              onChange={(e) => setPassage(+e.target.value)}
            >
              {test.passages.map((p) => (
                <option value={p.number} key={p.number}>
                  Passage {p.number} — {p.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Thời gian (phút)
            <input
              type="number"
              min={0}
              max={180}
              step={1}
              value={Number.isFinite(minutes) ? minutes : ""}
              onChange={(e) => setMinutes(e.target.valueAsNumber)}
            />
            <small className="muted">
              0 = không giới hạn. Có thể chọn từ 1 đến 180 phút.
            </small>
          </label>
          <p className="muted">
            Có thể tạm dừng. Đóng tab không tự dừng đồng hồ; hãy bấm Pause trước
            khi nghỉ.
          </p>
        </div>
      )}
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      <button
        className="button full"
        disabled={
          busy ||
          (mode === "practice" &&
            (!Number.isInteger(minutes) || minutes < 0 || minutes > 180))
        }
        onClick={begin}
      >
        {busy ? (
          <LoaderCircle size={17} className="spin" />
        ) : (
          <Play size={17} />
        )}
        Bắt đầu {mode === "exam" ? "thi thử" : "luyện tập"}
      </button>
    </Modal>
  );
}
function Settings({ refresh }: { refresh: () => Promise<void> }) {
  const [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  const restore = async (file: File) => {
    setBusy(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const r = await api<{ restored: number }>("/restore", {
        method: "POST",
        body: form,
      });
      setMessage(
        `Đã khôi phục ${r.restored} lượt làm bài. Lượt mới hơn trên máy được giữ nguyên.`
      );
      await refresh();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageTitle
        eyebrow="MỌI THỨ Ở NGAY ĐÂY"
        title="Cài đặt & sao lưu"
        text="Giữ an toàn cho lịch sử học tập trên máy của bạn."
      />
      <div className="content-panel settings-panel">
        <div className="panel-heading">
          <span className="stat-icon">
            <ShieldCheck size={22} />
          </span>
          <div>
            <h2>Dữ liệu của bạn, trên máy của bạn</h2>
            <p>
              Đáp án, ghi chú, highlight và phiên bản đề của từng lượt làm được
              lưu trong SQLite.
            </p>
          </div>
        </div>
        <div className="setting-row">
          <div>
            <strong>Xuất bản sao lưu</strong>
            <p>
              Tải tệp ZIP chứa toàn bộ lịch sử cùng nội dung đề gắn với các lượt
              làm.
            </p>
          </div>
          <a className="button secondary" href="/api/backup" download>
            <Download size={16} />
            Xuất dữ liệu
          </a>
        </div>
        <div className="setting-row">
          <div>
            <strong>Khôi phục bản sao lưu</strong>
            <p>
              Ghép các lượt làm từ tệp ZIP. Không ghi đè lượt có dữ liệu mới hơn
              trên máy.
            </p>
          </div>
          <label className={"button secondary " + (busy ? "disabled" : "")}>
            <Upload size={16} />
            {busy ? "Đang khôi phục…" : "Chọn tệp ZIP"}
            <input
              type="file"
              accept=".zip"
              disabled={busy}
              hidden
              onChange={(e) => {
                if (e.target.files?.[0]) void restore(e.target.files[0]);
                e.target.value = "";
              }}
            />
          </label>
        </div>
        {message && (
          <div className="info-box" role="status">
            {message}
          </div>
        )}
      </div>
      <div className="content-panel">
        <h2>Về phiên bản local</h2>
        <p>
          Ứng dụng dành cho IELTS Academic Reading và Listening, sử dụng một
          người trên máy Windows. Sau thiết lập ban đầu, bạn không cần kết nối
          Internet.
        </p>
        <p>
          Band chỉ mang tính tham khảo. Điểm chính xác được thể hiện bằng số câu
          đúng trên tổng số câu; luyện một passage không quy đổi thành band.
        </p>
        <p className="muted">
          Để bổ sung hoặc chỉnh nội dung đề, xem HƯỚNG_DẪN.md đi kèm ứng dụng.
          Việc chỉnh thư viện không thay đổi những lượt làm đã lưu.
        </p>
      </div>
    </>
  );
}

function Exam({ id, onBack }: { id: string; onBack: () => void }) {
  const {
    attempt: a,
    saveState,
    error,
    setError,
    edit,
    action,
    checkExpiry,
    flush,
    receivePlayback,
  } = useAttempt(id);
  const listening = a?.skill === "listening";
  const { preferences, update: updatePreferences } = useExamPreferences();
  const font = preferences.fontSize,
    setFont = (value: number) => updatePreferences({ fontSize: value });
  const [support, setSupport] = useState<"help" | "display" | "untimed" | null>(
    null
  );
  const [displayPassage, setDisplayPassage] = useState<number | null>(null);
  const [listeningClock, setListeningClock] = useState<number | null>(null),
    [transcript, setTranscript] = useState<{
      parts: Record<string, string>;
      provenance?: {
        transcriptNotice?: string;
        reconstructedFromProvidedAudio?: { parts: number[] };
      };
    } | null>(null);
  const [now, setNow] = useState(Date.now() / 1000),
    [split, setSplit] = useState(50),
    [submitOpen, setSubmitOpen] = useState(false),
    [busy, setBusy] = useState(false),
    [resultsOpen, setResultsOpen] = useState(false),
    [source, setSource] = useState<SourceImage[] | null>(null),
    [notesOpen, setNotesOpen] = useState(false);
  const [selection, setSelection] = useState<{
    x: number;
    y: number;
    ranges: TextRange[];
  } | null>(null);
  const [noteEditing, setNoteEditing] = useState<Annotation | null>(null),
    [noteText, setNoteText] = useState("");
  const [focused, setFocused] = useState<number | null>(null);
  const expiryRequested = useRef(false),
    panels = useRef<HTMLDivElement>(null),
    reading = useRef<HTMLDivElement>(null),
    questions = useRef<HTMLDivElement>(null);
  const offset = useRef(0);
  useEffect(() => {
    if (a) offset.current = a.serverNow - Date.now() / 1000;
  }, [a?.serverNow]);
  useEffect(() => {
    const t = setInterval(
      () => setNow(Date.now() / 1000 + offset.current),
      1000
    );
    return () => clearInterval(t);
  }, []);
  const remaining =
    a?.deadline != null
      ? Math.max(0, Math.ceil(a.deadline - now))
      : a?.remaining == null
      ? a?.remaining
      : Math.max(0, Math.ceil(a.remaining));
  useEffect(() => {
    if (
      a?.status === "active" &&
      a.deadline &&
      remaining === 0 &&
      !expiryRequested.current
    ) {
      expiryRequested.current = true;
      void checkExpiry().catch((e) => {
        setError(e.message);
        expiryRequested.current = false;
      });
    }
  }, [a?.status, a?.deadline, remaining, now, checkExpiry, setError]);
  useEffect(() => {
    reading.current?.scrollTo({ top: 0 });
    questions.current?.scrollTo({ top: 0 });
    setSelection(null);
  }, [a?.currentPassage, displayPassage]);
  const perform = async (name: string) => {
    setBusy(true);
    try {
      await action(name);
      if (name === "grade") setResultsOpen(true);
      if (name === "submit") setSubmitOpen(false);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const goBack = async () => {
    try {
      await flush();
      onBack();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const changePassage = (n: number) => {
    if (a?.status === "active") edit({ currentPassage: n });
    setDisplayPassage(n);
    setFocused(
      a?.test.passages.find((p) => p.number === n)?.groups[0]?.questions[0]
        ?.number ?? null
    );
  };
  const p =
    a?.test.passages.find(
      (p) => p.number === (displayPassage ?? a.currentPassage)
    ) || a?.test.passages[0];
  const isActive = a?.status === "active",
    editable =
      isActive &&
      (remaining === undefined || remaining === null || remaining > 0);
  const jump = (n: number) => {
    if (!a) return;
    const passage = a.test.passages.find((p) =>
      p.groups.some((g) => g.questions.some((q) => q.number === n))
    );
    if (passage) {
      const group = passage.groups.find((g) =>
        g.questions.some((q) => q.number === n)
      );
      const target = group?.type === "multi" ? group.questions[0].number : n;
      changePassage(passage.number);
      setFocused(n);
      setTimeout(() => {
        const el = document.querySelector<HTMLElement>(
          '[data-question="' + target + '"]'
        );
        el?.scrollIntoView({ behavior: "smooth", block: "center" });
        (
          el?.querySelector<HTMLElement>(
            "input:not(:disabled),select:not(:disabled),textarea:not(:disabled)"
          ) || el?.querySelector<HTMLElement>("button:not(:disabled)")
        )?.focus({ preventScroll: true });
      }, 80);
    }
  };
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (
        e.altKey &&
        (e.key === "ArrowRight" || e.key === "ArrowLeft") &&
        a &&
        !document.querySelector("[role=dialog]")
      ) {
        e.preventDefault();
        const index = a.numbers.indexOf(focused ?? a.numbers[0]);
        jump(
          a.numbers[
            Math.max(
              0,
              Math.min(
                a.numbers.length - 1,
                index + (e.key === "ArrowRight" ? 1 : -1)
              )
            )
          ]
        );
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  });
  const selectText = (e: React.MouseEvent) => {
    if (!editable || !a) return;
    const s = window.getSelection();
    if (!s?.rangeCount || s.isCollapsed || !s.toString().trim()) {
      setSelection(null);
      return;
    }
    const range = s.getRangeAt(0),
      ranges: TextRange[] = [];
    panels.current
      ?.querySelectorAll<HTMLElement>("[data-text-id]")
      .forEach((el) => {
        if (!range.intersectsNode(el) || !el.textContent) return;
        let start = 0,
          end = el.textContent.length;
        if (el.contains(range.startContainer)) {
          const before = range.cloneRange();
          before.selectNodeContents(el);
          before.setEnd(range.startContainer, range.startOffset);
          start = before.toString().length;
        }
        if (el.contains(range.endContainer)) {
          const before = range.cloneRange();
          before.selectNodeContents(el);
          before.setEnd(range.endContainer, range.endOffset);
          end = before.toString().length;
        }
        if (end > start)
          ranges.push({
            anchor: el.dataset.textId!,
            start,
            end,
            text: el.textContent.slice(start, end),
          });
      });
    if (ranges.length)
      setSelection({
        x: Math.min(window.innerWidth - 350, Math.max(12, e.clientX)),
        y: Math.max(135, e.clientY - 48),
        ranges,
      });
  };
  const annotate = (kind: "highlight" | "note" | "clear" = "highlight") => {
    if (!a || !selection) return;
    if (kind === "note") {
      setNoteEditing({
        ...selection.ranges[0],
        id: crypto.randomUUID(),
        kind: "note",
        note: "",
      });
      setNoteText("");
    } else
      edit((current) => ({
        annotations: highlightSelection(
          current.annotations,
          selection.ranges,
          kind === "clear"
        ),
      }));
    setSelection(null);
    window.getSelection()?.removeAllRanges();
  };
  const drag = (e: React.PointerEvent) => {
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const dragMove = (e: React.PointerEvent) => {
    if (e.buttons !== 1) return;
    const rect = panels.current?.getBoundingClientRect();
    if (rect)
      setSplit(
        Math.max(32, Math.min(68, ((e.clientX - rect.left) / rect.width) * 100))
      );
  };
  if (!a || !p)
    return (
      <div className="exam-loading">
        <BookOpen size={34} />
        {error ? (
          <>
            <p>{error}</p>
            <button className="button" onClick={onBack}>
              Về thư viện
            </button>
          </>
        ) : (
          <>
            <LoaderCircle className="spin" />
            <p>Đang mở bài làm của bạn…</p>
          </>
        )}
      </div>
    );
  const readonly = a.status === "submitted" || a.status === "graded";
  const resultMap = Object.fromEntries(
    (a.result?.rows || []).map((r) => [r.number, r])
  );
  const untimed = a.mode === "exam" && a.examTiming === "untimed";
  const elapsed = Math.max(
    0,
    Math.floor(
      (a.elapsedSeconds || 0) +
        (a.elapsedStartedAt == null ? 0 : now - a.elapsedStartedAt)
    )
  );
  const elapsedClock =
    (elapsed >= 3600
      ? Math.floor(elapsed / 3600)
          .toString()
          .padStart(2, "0") + ":"
      : "") +
    Math.floor((elapsed / 60) % 60)
      .toString()
      .padStart(2, "0") +
    ":" +
    (elapsed % 60).toString().padStart(2, "0");
  const clock = listening
    ? clockText(
        listeningClock ??
          (a.mode === "exam" ? listeningRemaining(a) : a.player!.elapsed)
      )
    : untimed
    ? elapsedClock
    : remaining == null
    ? "Untimed"
    : `${Math.floor(remaining / 60)
        .toString()
        .padStart(2, "0")}:${(remaining % 60).toString().padStart(2, "0")}`;
  const timerRemaining =
    listening && a.mode === "exam"
      ? listeningClock ?? listeningRemaining(a)
      : remaining;
  const playerView = listening ? (
    <ListeningPlayer
      attempt={a}
      displayPart={p.number}
      receive={receivePlayback}
      flush={flush}
      error={setError}
      onClock={setListeningClock}
      onPlayingPart={changePassage}
      onTranscript={() => {
        void api<NonNullable<typeof transcript>>(
          "/attempts/" + id + "/transcript"
        )
          .then((t) => setTranscript(t))
          .catch((e) => setError(e.message));
      }}
    />
  ) : null;
  const displayNote = (ann: Annotation) => {
    setNoteEditing(ann);
    setNoteText(ann.note || "");
  };
  return (
    <div
      className={
        "exam-shell " +
        (listening ? "listening-shell" : "") +
        " theme-" +
        preferences.contrast
      }
    >
      <header className="exam-header">
        <button
          className="icon-button"
          title="Back to library"
          aria-label="Back to library"
          onClick={goBack}
        >
          <ArrowLeft size={20} />
        </button>
        <div className="exam-identity">
          <strong>{a.title}</strong>
          <span>
            {listening ? "LISTENING" : "ACADEMIC READING"} <i />{" "}
            {a.mode === "exam"
              ? "MOCK TEST"
              : listening
              ? a.part
                ? "PART PRACTICE"
                : "FULL PRACTICE"
              : "PASSAGE PRACTICE"}
          </span>
        </div>
        <div
          className={
            "timer " +
            (!readonly &&
            a.status === "active" &&
            timerRemaining != null &&
            timerRemaining < 300
              ? "urgent"
              : "")
          }
        >
          <Clock3 size={20} />
          <div>
            <small>
              {readonly
                ? "COMPLETED"
                : a.status === "paused"
                ? "PAUSED"
                : untimed || (listening && a.mode === "practice")
                ? "TIME ELAPSED"
                : "TIME REMAINING"}
            </small>
            <strong>{readonly ? "Review" : clock}</strong>
          </div>
        </div>
        <span className="sr-only" role="status">
          {!readonly &&
          a.status === "active" &&
          timerRemaining != null &&
          timerRemaining < 60
            ? "Less than one minute remaining."
            : !readonly &&
              a.status === "active" &&
              timerRemaining != null &&
              timerRemaining < 300
            ? "Less than five minutes remaining."
            : ""}
        </span>
        <div className="exam-header-actions">
          <span className={"save-status " + saveState} role="status">
            {saveState === "saving" || saveState === "pending" ? (
              <LoaderCircle size={13} className="spin" />
            ) : saveState === "saved" ? (
              <Check size={14} />
            ) : (
              <WifiOff size={14} />
            )}
            {
              {
                saved: "Saved on this device",
                pending: "Saving…",
                saving: "Saving…",
                offline: "Draft saved in browser",
                conflict: "Save conflict",
              }[saveState]
            }
          </span>
          {!listening &&
            (a.mode === "practice" || untimed) &&
            a.status === "active" && (
              <button
                className="button secondary small"
                onClick={() => perform("pause")}
                disabled={busy}
              >
                <Pause size={15} />
                Pause
              </button>
            )}
          {!listening &&
            a.mode === "exam" &&
            !untimed &&
            a.status === "active" && (
              <button
                className="button secondary small switch-untimed"
                disabled={busy}
                onClick={() => setSupport("untimed")}
              >
                Switch to untimed
              </button>
            )}
          {!readonly && (
            <button
              className="button small"
              onClick={() => setSubmitOpen(true)}
              disabled={busy}
            >
              Finish test
              <ArrowRight size={15} />
            </button>
          )}
          {a.status === "submitted" && (
            <button
              className="button small"
              disabled={busy}
              onClick={() => perform("grade")}
            >
              Chấm bài
              <CheckCircle2 size={16} />
            </button>
          )}
          {a.result && (
            <button
              className="button small"
              onClick={() => setResultsOpen(true)}
            >
              Xem kết quả
              <ChartNoAxesCombined size={16} />
            </button>
          )}
        </div>
      </header>
      {error && (
        <div className="exam-alert" role="alert">
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Dismiss">
            <X size={15} />
          </button>
          {saveState === "conflict" && (
            <button
              onClick={() => {
                const blob = new Blob(
                    [localStorage.getItem("reading-room:draft:" + id) || "{}"],
                    { type: "application/json" }
                  ),
                  url = URL.createObjectURL(blob),
                  link = document.createElement("a");
                link.href = url;
                link.download = "reading-room-draft.json";
                link.click();
                URL.revokeObjectURL(url);
              }}
            >
              Xuất bản nháp
            </button>
          )}
        </div>
      )}
      {readonly && (
        <div className={"review-banner " + (a.result ? "graded" : "")}>
          <CheckCircle2 size={17} />
          {a.result ? (
            <>
              <strong>
                {a.result.score}/{a.result.total} câu đúng
              </strong>
              {a.result.band !== null && (
                <span>Band tham khảo {a.result.band}</span>
              )}
              <span>Đối chiếu đáp án của bạn bên dưới.</span>
            </>
          ) : (
            <>
              <strong>Đã nộp bài{a.autoSubmitted ? " do hết giờ" : ""}.</strong>
              <span>
                Đây là đáp án bạn đã điền. Khi sẵn sàng, bấm “Chấm bài” để xem
                kết quả.
              </span>
            </>
          )}
        </div>
      )}
      {!transcript && playerView}
      <div className="exam-toolbar">
        <div className="passage-tabs" role="group" aria-label="Test parts">
          {visibleUnits(a).map((pa) => (
            <button
              key={pa.number}
              onClick={() => changePassage(pa.number)}
              aria-pressed={pa.number === p.number}
              className={pa.number === p.number ? "selected" : ""}
            >
              {listening ? "Part" : "Passage"} {pa.number}
              <span>
                {
                  pa.groups
                    .flatMap((g) => g.questions)
                    .filter((q) => a.answers[q.number]?.trim()).length
                }
                /{pa.groups.flatMap((g) => g.questions).length}
              </span>
            </button>
          ))}
        </div>
        <div className="reading-tools">
          <button onClick={() => setSupport("display")}>
            <Settings2 size={16} />
            Display
          </button>
          <button onClick={() => setSupport("help")}>
            <HelpCircle size={16} />
            Help
          </button>
          <button
            className="quick-text-size"
            title="Smaller text"
            aria-label="Smaller text"
            onClick={() => setFont(Math.max(14, font - 1))}
          >
            A−
          </button>
          <button
            className="quick-text-size"
            title="Larger text"
            aria-label="Larger text"
            onClick={() => setFont(Math.min(24, font + 1))}
          >
            A+
          </button>
          <span />
          <button onClick={() => setNotesOpen(true)}>
            <StickyNote size={16} />
            Notes{" "}
            <small>
              {a.annotations.filter((n) => n.kind === "note").length || ""}
            </small>
          </button>
          <button
            title="Fullscreen"
            aria-label="Fullscreen"
            onClick={() => {
              if (document.fullscreenElement) void document.exitFullscreen();
              else
                void document.documentElement
                  .requestFullscreen()
                  .catch(() => {});
            }}
          >
            <Maximize2 size={17} />
          </button>
        </div>
      </div>
      <div
        ref={panels}
        className="exam-panels"
        onMouseUp={selectText}
        style={{ "--reading-size": font + "px" } as React.CSSProperties}
      >
        {!listening && (
          <section
            className="reading-pane"
            ref={reading}
            style={{ width: split + "%" }}
            aria-label="Reading passage"
          >
            <div className="pane-caption">
              <span>READING PASSAGE {p.number}</span>
              {!!p.sourceImages?.length && (
                <button
                  className="source-link"
                  onClick={() => setSource(p.sourceImages!)}
                >
                  <Search size={13} />
                  Source
                </button>
              )}
            </div>
            <h1>{p.title}</h1>
            <p className="reading-instruction">
              You should spend about 20 minutes on Questions{" "}
              {p.groups[0]?.questions[0]?.number}–
              {p.groups.at(-1)?.questions.at(-1)?.number}, which are based on
              Reading Passage {p.number}.
            </p>
            <div className="passage-text">
              {p.paragraphs.map((par) => (
                <p key={par.id} className={par.kind}>
                  {par.label && (
                    <strong className="paragraph-label">{par.label}</strong>
                  )}
                  <Annotated
                    id={par.id}
                    text={par.text}
                    annotations={a.annotations}
                    onEdit={displayNote}
                  />
                </p>
              ))}
            </div>
            <div className="passage-end">
              <span />
              End of passage
              <span />
            </div>
          </section>
        )}
        {!listening && (
          <div
            className="splitter"
            role="separator"
            aria-label="Resize reading and question panes"
            aria-orientation="vertical"
            aria-valuemin={32}
            aria-valuemax={68}
            aria-valuenow={Math.round(split)}
            tabIndex={0}
            onPointerDown={drag}
            onPointerMove={dragMove}
            onKeyDown={(e) => {
              if (e.key === "ArrowLeft") {
                e.preventDefault();
                setSplit(Math.max(32, split - 2));
              }
              if (e.key === "ArrowRight") {
                e.preventDefault();
                setSplit(Math.min(68, split + 2));
              }
            }}
          >
            <i />
            <i />
            <i />
          </div>
        )}
        <section
          className="questions-pane"
          ref={questions}
          style={{ width: listening ? "100%" : 100 - split + "%" }}
          aria-label="Questions"
        >
          <div className="pane-caption">
            <span>QUESTIONS</span>
            <span>
              {listening ? "Part" : "Passage"} {p.number}
            </span>
          </div>
          {p.groups.map((g) => (
            <QuestionGroup
              key={g.id}
              group={g}
              attempt={a}
              editable={!!editable}
              onAnswer={(n, value) =>
                edit((current) => ({
                  answers: { ...current.answers, [n]: value },
                }))
              }
              onAnswerPart={(n, part, count, value) =>
                edit((current) => {
                  const values = answerPartsFor(current, n, count);
                  values[part] = value;
                  return {
                    answerParts: { ...current.answerParts, [n]: values },
                    answers: {
                      ...current.answers,
                      [n]: values.join(" ").trim(),
                    },
                  };
                })
              }
              onMulti={(nums, values) =>
                edit((current) => {
                  const next = { ...current.answers };
                  nums.forEach((n, i) => (next[n] = values[i] || ""));
                  return { answers: next };
                })
              }
              onFlag={(n) =>
                edit((current) => ({
                  flags: current.flags.includes(n)
                    ? current.flags.filter((x) => x !== n)
                    : [...current.flags, n],
                }))
              }
              onFocus={setFocused}
              focused={focused}
              results={resultMap}
              source={setSource}
              onAnnotation={displayNote}
            />
          ))}
        </section>
        {a.status === "paused" && (
          <div className="pause-overlay">
            <div>
              <span className="pause-symbol">
                <Pause size={30} />
              </span>
              <h2>Take a little break.</h2>
              <p>
                Your time and answers are saved.
                <br />
                Continue whenever you are ready.
              </p>
              <button
                className="button"
                disabled={busy}
                onClick={() =>
                  listening
                    ? document
                        .querySelector<HTMLButtonElement>(
                          ".listening-player [data-audio-resume]"
                        )
                        ?.click()
                    : perform("resume")
                }
              >
                <Play size={17} />
                Resume
              </button>
            </div>
          </div>
        )}
      </div>
      <ExamNavigation
        units={visibleUnits(a)}
        answers={a.answers}
        flags={a.flags}
        current={focused ?? p.groups[0]?.questions[0]?.number ?? a.numbers[0]}
        activePart={p.number}
        results={resultMap}
        onJump={jump}
        onPart={changePassage}
      />
      {support === "help" && (
        <Modal
          title="Help · Test controls"
          onClose={() => setSupport(null)}
          wide
        >
          <ExamHelp
            skill={listening ? "listening" : "reading"}
            practice={a.mode === "practice" || a.examTiming === "untimed"}
          />
        </Modal>
      )}
      {support === "display" && (
        <Modal title="Display settings" onClose={() => setSupport(null)}>
          <DisplaySettings value={preferences} onChange={updatePreferences} />
        </Modal>
      )}
      {support === "untimed" && (
        <Modal title="Switch to untimed?" onClose={() => setSupport(null)}>
          <p>
            Your answers, flags and notes will be kept. The clock will count up,
            and Pause will become available.
          </p>
          <p>You cannot switch this attempt back to the timed test.</p>
          <div className="modal-actions">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => setSupport(null)}
            >
              Keep timed test
            </button>
            <button
              className="button"
              disabled={busy}
              onClick={() => {
                setSupport(null);
                void perform("untimed");
              }}
            >
              Switch to untimed
            </button>
          </div>
        </Modal>
      )}

      {selection && (
        <div
          className="selection-menu"
          style={{ left: selection.x, top: selection.y }}
          onMouseDown={(e) => e.preventDefault()}
        >
          <button onClick={() => annotate()}>
            <Highlighter size={15} />
            Highlight
          </button>
          <button onClick={() => annotate("note")}>
            <StickyNote size={15} />
            Note
          </button>
          <button onClick={() => annotate("clear")}>
            <Eraser size={15} />
            Clear highlight
          </button>
        </div>
      )}
      {submitOpen && (
        <Modal title="Finish your test?" onClose={() => setSubmitOpen(false)}>
          <div className="submit-summary">
            <CheckCircle2 size={30} />
            <strong>
              {answered(a)} / {a.numbers.length}
            </strong>
            <span>questions answered</span>
          </div>
          {answered(a) < a.numbers.length && (
            <div className="info-box">
              You have{" "}
              <strong>
                {a.numbers.length - answered(a)} unanswered questions
              </strong>
              . You can return to your test and check them before submitting.
            </div>
          )}
          <div className="submit-review-actions">
            <button
              className="button secondary"
              disabled={busy || !a.numbers.some((n) => !a.answers[n]?.trim())}
              onClick={() => {
                setSubmitOpen(false);
                const n = a.numbers.find((n) => !a.answers[n]?.trim());
                if (n !== undefined) jump(n);
              }}
            >
              Review unanswered
            </button>
            <button
              className="button secondary"
              disabled={busy || a.flags.length === 0}
              onClick={() => {
                setSubmitOpen(false);
                if (a.flags[0] !== undefined) jump(a.flags[0]);
              }}
            >
              Review flagged ({a.flags.length})
            </button>
          </div>
          <p className="muted">
            Your answers will be locked after submission. You can review them
            before choosing to see your score.
          </p>
          <div className="modal-actions">
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => setSubmitOpen(false)}
            >
              Keep working
            </button>
            <button
              className="button"
              disabled={busy}
              onClick={() => perform("submit")}
            >
              {busy ? (
                <LoaderCircle size={16} className="spin" />
              ) : (
                <Check size={16} />
              )}
              Submit answers
            </button>
          </div>
        </Modal>
      )}
      {a.result && resultsOpen && (
        <Modal
          title={"Kết quả bài " + (listening ? "Listening" : "Reading")}
          onClose={() => setResultsOpen(false)}
          wide
        >
          <div className="score-overview">
            <div>
              <span>SỐ CÂU ĐÚNG</span>
              <strong>
                {a.result.score}
                <small>/{a.result.total}</small>
              </strong>
            </div>
            {a.result.band !== null && (
              <div>
                <span>BAND THAM KHẢO</span>
                <strong>{a.result.band.toFixed(1)}</strong>
              </div>
            )}
            <div>
              <span>CHƯA TRẢ LỜI</span>
              <strong>{a.result.blank}</strong>
            </div>
          </div>
          <p className="muted">
            {a.result.band !== null
              ? "Band là mức quy đổi tham khảo; ngưỡng điểm chính thức có thể thay đổi theo đề."
              : "Bài luyện một passage chỉ tính số câu đúng, không quy đổi band."}
          </p>
          <PassageBreakdown result={a.result} listening={listening} />
          <TypeBreakdown results={[a.result]} />
          <div className="answer-table">
            <div className="answer-table-head">
              <span>Câu</span>
              <span>Bạn đã trả lời</span>
              <span>Đáp án chấp nhận</span>
              <span>Kết quả</span>
            </div>
            {a.result.rows.map((r) => (
              <button
                className="answer-table-row"
                key={r.number}
                onClick={() => {
                  setResultsOpen(false);
                  jump(r.number);
                }}
              >
                <strong>{r.number}</strong>
                <span>{r.answer || "—"}</span>
                <span>
                  {r.accepted.join(" / ")}
                  {r.groupNumbers && (
                    <small>
                      Nhóm {r.groupNumbers.join("–")}, không xét thứ tự
                    </small>
                  )}
                </span>
                <span className={"answer-status " + r.status}>
                  {r.status === "correct"
                    ? "Đúng"
                    : r.status === "blank"
                    ? "Bỏ trống"
                    : "Sai"}
                </span>
              </button>
            ))}
          </div>
        </Modal>
      )}
      {transcript && (
        <Modal
          title={"Transcript · Part " + p.number}
          onClose={() => setTranscript(null)}
          wide
        >
          <div className="transcript-player">{playerView}</div>
          <div className="transcript-parts">
            {visibleUnits(a).map((u) => (
              <button
                className={p.number === u.number ? "selected" : ""}
                key={u.number}
                onClick={() => changePassage(u.number)}
              >
                Part {u.number}
              </button>
            ))}
          </div>
          <div className="transcript-text">
            {(transcript.provenance?.transcriptNotice ||
              transcript.provenance?.reconstructedFromProvidedAudio?.parts.includes(
                p.number
              )) && (
              <p className="info-box">
                {transcript.provenance?.transcriptNotice ||
                  "PDF nguồn thiếu đoạn audioscript. Đoạn thiếu được khôi phục từ audio đã cung cấp; bản chép có thể còn sai khác nhỏ về từ ngữ."}
              </p>
            )}
            {transcript.parts[String(p.number)] ||
              "Transcript chưa có cho Part này."}
          </div>
        </Modal>
      )}
      {source && (
        <SourceViewer images={source} onClose={() => setSource(null)} />
      )}
      {notesOpen && (
        <Modal title="Your notes" onClose={() => setNotesOpen(false)}>
          <p className="muted">
            Select text in the passage or questions, then choose Note.
          </p>
          {a.annotations.some((ann) => ann.kind === "note") ? (
            a.annotations
              .filter((ann) => ann.kind === "note")
              .map((ann) => (
                <div className="annotation-card" key={ann.id}>
                  <blockquote>{ann.text}</blockquote>
                  {ann.note && <p>{ann.note}</p>}
                  <button
                    className="text-button"
                    onClick={() => {
                      setNotesOpen(false);
                      displayNote(ann);
                    }}
                  >
                    {editable ? "Edit note" : "View note"}
                  </button>
                </div>
              ))
          ) : (
            <div className="empty">
              <StickyNote size={28} />
              <p>No notes yet. Make the passage your own.</p>
            </div>
          )}
        </Modal>
      )}
      {noteEditing && (
        <Modal
          title={editable ? "Note for selected text" : "Your note"}
          onClose={() => setNoteEditing(null)}
        >
          <blockquote className="note-quote">{noteEditing.text}</blockquote>
          <textarea
            rows={5}
            maxLength={5000}
            placeholder="What would you like to remember?"
            value={noteText}
            readOnly={!editable}
            onChange={(e) => setNoteText(e.target.value)}
          />
          {editable && (
            <div className="modal-actions">
              <button
                className="button secondary"
                onClick={() => {
                  edit((current) => ({
                    annotations: current.annotations.filter(
                      (x) => x.id !== noteEditing.id
                    ),
                  }));
                  setNoteEditing(null);
                }}
              >
                Delete note
              </button>
              <button
                className="button"
                onClick={() => {
                  edit((current) => ({
                    annotations: [
                      ...current.annotations.filter(
                        (x) => x.id !== noteEditing.id
                      ),
                      { ...noteEditing, note: noteText },
                    ],
                  }));
                  setNoteEditing(null);
                }}
              >
                Save note
              </button>
            </div>
          )}
        </Modal>
      )}
    </div>
  );
}

function QuestionGroup({
  group: g,
  attempt: a,
  editable,
  onAnswer,
  onAnswerPart,
  onMulti,
  onFlag,
  onFocus,
  focused,
  results,
  source,
  onAnnotation,
}: {
  group: Group;
  attempt: Attempt;
  editable: boolean;
  onAnswer: (n: number, v: string) => void;
  onAnswerPart: (n: number, part: number, count: number, v: string) => void;
  onMulti: (nums: number[], values: string[]) => void;
  onFlag: (n: number) => void;
  onFocus: (n: number) => void;
  focused: number | null;
  results: Record<number, NonNullable<Attempt["result"]>["rows"][number]>;
  source: (s: SourceImage[]) => void;
  onAnnotation: (a: Annotation) => void;
}) {
  const nums = g.questions.map((q) => q.number);
  const textBody = g.body?.trim();
  const imageMode = g.renderMode === "source" && !!g.sourceImages?.length;
  const allHaveText = g.questions.every(
    (q) => q.text?.trim() && q.text.trim() !== String(q.number)
  );
  const showBody =
    imageMode ||
    g.type === "completion" ||
    g.type === "short" ||
    g.type === "matching" ||
    !allHaveText;
  const blanks = [
    ...(g.body || "").matchAll(/\b(\d{1,2})\s*(?:_{3,}|[.…·]{3,})/g),
  ].filter((m) => nums.includes(+m[1]));
  const inline =
    g.type === "completion" &&
    !imageMode &&
    new Set(blanks.map((m) => +m[1])).size === nums.length &&
    blanks.length === nums.length;
  const optionLabel = (o: Option) =>
    o.label === o.value
      ? o.value
      : o.label?.startsWith(o.value + ".")
      ? o.label
      : `${o.value}. ${o.label}`;
  const optsFor = (q: { options?: Option[] }) => q.options || g.options || [];
  const flag = (n: number) => (
    <button
      className={"flag-button " + (a.flags.includes(n) ? "flagged" : "")}
      aria-label={"Mark question " + n + " for review"}
      aria-pressed={a.flags.includes(n)}
      title="Mark for review"
      disabled={!editable}
      onClick={() => onFlag(n)}
    >
      <Flag size={14} />
    </button>
  );
  if (a.skill === "listening" && g.type === "matching" && !g.layout)
    return (
      <div className="question-group">
        <div className="group-heading">
          <h2>{g.heading}</h2>
          {!!g.sourceImages?.length && (
            <button
              className="source-link"
              onClick={() => source(g.sourceImages!)}
            >
              Source
            </button>
          )}
        </div>
        <div className="group-instructions">
          <Annotated
            id={g.id + "-instructions"}
            text={g.instructions || ""}
            annotations={a.annotations}
            onEdit={onAnnotation}
          />
        </div>
        <ListeningMatching
          {...{
            group: g,
            attempt: a,
            editable,
            results,
            onAnswer,
            onAnswerPart,
            onFlag,
            onFocus,
            onAnnotation,
          }}
        />
      </div>
    );
  if (g.layout) {
    const props = {
      group: g,
      attempt: a,
      editable,
      results,
      onAnswer,
      onAnswerPart,
      onFlag,
      onFocus,
      onAnnotation,
    };
    return (
      <div className="question-group">
        <div className="group-heading">
          <h2>{g.heading}</h2>
          {!!g.sourceImages?.length && (
            <button
              className="source-link"
              onClick={() => source(g.sourceImages!)}
            >
              <Search size={13} />
              Source
            </button>
          )}
        </div>
        <div className="group-instructions">
          <Annotated
            id={g.id + "-instructions"}
            text={g.instructions || ""}
            annotations={a.annotations}
            onEdit={onAnnotation}
          />
        </div>
        {g.layout.kind === "table" ? (
          <InteractiveTable {...props} />
        ) : g.layout.kind === "matrix" ? (
          <MatchingMatrix {...props} />
        ) : (
          <ExtendedLayout {...props} />
        )}
      </div>
    );
  }
  return (
    <div className="question-group">
      <div className="group-heading">
        <h2>{g.heading || `Questions ${nums[0]}–${nums.at(-1)}`}</h2>
        {!!g.sourceImages?.length && (
          <button
            className="source-link"
            onClick={() => source(g.sourceImages!)}
          >
            <Search size={13} />
            Source
          </button>
        )}
      </div>
      <div className="group-instructions">
        <Annotated
          id={g.id + "-instructions"}
          text={g.instructions || ""}
          annotations={a.annotations}
          onEdit={onAnnotation}
        />
      </div>
      {showBody && textBody && !imageMode && !inline && (
        <div className="task-body">
          <Annotated
            id={g.id + "-body"}
            text={textBody}
            annotations={a.annotations}
            onEdit={onAnnotation}
          />
        </div>
      )}
      {inline && (
        <div className="task-body inline-task">
          {blanks.map((m, i) => {
            const start =
                i === 0 ? 0 : blanks[i - 1].index! + blanks[i - 1][0].length,
              n = +m[1];
            return (
              <React.Fragment key={n}>
                <Annotated
                  id={g.id + "-body-" + start}
                  text={g.body.slice(start, m.index)}
                  annotations={a.annotations}
                  onEdit={onAnnotation}
                />
                <span
                  className={"inline-blank " + (results[n]?.status || "")}
                  data-question={n}
                  onFocus={() => onFocus(n)}
                >
                  <label htmlFor={"answer-" + n}>{n}</label>
                  <input
                    id={"answer-" + n}
                    aria-label={"Answer " + n}
                    value={a.answers[n] || ""}
                    disabled={!editable}
                    autoComplete="off"
                    spellCheck={false}
                    maxLength={1000}
                    onChange={(e) => onAnswer(n, e.target.value)}
                  />
                  {flag(n)}
                </span>
              </React.Fragment>
            );
          })}
          <Annotated
            id={g.id + "-body-end"}
            text={g.body.slice(
              blanks.at(-1)!.index! + blanks.at(-1)![0].length
            )}
            annotations={a.annotations}
            onEdit={onAnnotation}
          />
          {nums.map(
            (n) => results[n] && <AnswerFeedback key={n} row={results[n]} />
          )}
        </div>
      )}
      {imageMode && (
        <div className="task-source-images">
          {g.sourceImages!.map((s, i) => (
            <img
              key={i}
              src={s.url}
              loading="lazy"
              alt={"Original question layout for " + g.heading}
            />
          ))}
        </div>
      )}
      {g.type === "matching" &&
        !imageMode &&
        !!g.options?.length &&
        g.options.some((o) => o.label !== o.value) &&
        !g.options.every((o) => textBody?.includes(o.label)) && (
          <div className="matching-options" aria-label="List of options">
            {g.options.map((o) => (
              <div key={o.value}>
                <strong>{o.value}</strong>
                <span>{o.label}</span>
              </div>
            ))}
          </div>
        )}
      {inline ? null : g.type === "multi" ? (
        <div
          className="multi-question"
          data-question={nums[0]}
          onFocus={() => onFocus(nums[0])}
        >
          <div className="multi-label">
            <strong>{nums.join(" & ")}</strong>
            <span>Choose {g.choose || nums.length} answers.</span>
            {nums.map((n) => (
              <React.Fragment key={n}>{flag(n)}</React.Fragment>
            ))}
          </div>
          {!showBody && g.questions[0]?.text && (
            <p>
              <Annotated
                id={g.id + "-prompt"}
                text={g.questions[0].text}
                annotations={a.annotations}
                onEdit={onAnnotation}
              />
            </p>
          )}
          {(g.options || []).map((o) => {
            const selected = nums.some((n) => a.answers[n] === o.value),
              count = nums.filter((n) => a.answers[n]).length;
            return (
              <label
                className={"option " + (selected ? "chosen" : "")}
                key={o.value}
              >
                <input
                  type="checkbox"
                  checked={selected}
                  disabled={
                    !editable ||
                    (!selected && count >= (g.choose || nums.length))
                  }
                  onChange={() => {
                    const chosen = nums
                      .map((n) => a.answers[n])
                      .filter(Boolean);
                    onMulti(
                      nums,
                      selected
                        ? chosen.filter((v) => v !== o.value)
                        : [...chosen, o.value]
                    );
                  }}
                />
                <span>{optionLabel(o)}</span>
              </label>
            );
          })}
          {!g.options?.length && (
            <div className="inline-answers">
              {nums.map((n) => (
                <label key={n}>
                  {n}
                  <input
                    aria-label={"Answer " + n}
                    value={a.answers[n] || ""}
                    disabled={!editable}
                    onChange={(e) => onAnswer(n, e.target.value)}
                  />
                </label>
              ))}
            </div>
          )}
          {nums.map(
            (n) => results[n] && <AnswerFeedback key={n} row={results[n]} />
          )}
        </div>
      ) : (
        g.questions.map((q) => {
          const opts =
            g.type === "tfng"
              ? [
                  { value: "TRUE", label: "TRUE" },
                  { value: "FALSE", label: "FALSE" },
                  { value: "NOT GIVEN", label: "NOT GIVEN" },
                ]
              : g.type === "ynng"
              ? [
                  { value: "YES", label: "YES" },
                  { value: "NO", label: "NO" },
                  { value: "NOT GIVEN", label: "NOT GIVEN" },
                ]
              : optsFor(q);
          const isChoice = g.type === "choice" && opts.length > 0;
          const showStem =
            !showBody ||
            (g.type === "matching" &&
              !imageMode &&
              !!q.text?.trim() &&
              !textBody?.includes(q.text));
          return (
            <div
              data-question={q.number}
              key={q.number}
              onFocus={() => onFocus(q.number)}
              className={
                "question-item " +
                (focused === q.number ? "question-focused" : "") +
                " " +
                (results[q.number]?.status || "")
              }
            >
              <div className="question-label">
                <span className="question-index">{q.number}</span>
                {showStem && (
                  <span className="question-text">
                    <Annotated
                      id={g.id + "-q" + q.number}
                      text={q.text}
                      annotations={a.annotations}
                      onEdit={onAnnotation}
                    />
                  </span>
                )}
                {!showStem && (
                  <label
                    htmlFor={"answer-" + q.number}
                    className="answer-label"
                  >
                    Answer {q.number}
                  </label>
                )}
                {flag(q.number)}
              </div>
              {isChoice ? (
                <div className="question-options">
                  {opts.map((o) => (
                    <label
                      key={o.value}
                      className={
                        "option " +
                        (a.answers[q.number] === o.value ? "chosen" : "")
                      }
                    >
                      <input
                        type="radio"
                        name={"q-" + q.number}
                        value={o.value}
                        checked={a.answers[q.number] === o.value}
                        disabled={!editable}
                        onChange={() => onAnswer(q.number, o.value)}
                      />
                      <span>{optionLabel(o)}</span>
                    </label>
                  ))}
                  {editable && a.answers[q.number] && (
                    <button
                      className="text-button clear-answer"
                      onClick={() => onAnswer(q.number, "")}
                    >
                      Clear answer
                    </button>
                  )}
                </div>
              ) : opts.length > 0 ? (
                <select
                  id={"answer-" + q.number}
                  aria-label={"Answer " + q.number}
                  value={a.answers[q.number] || ""}
                  disabled={!editable}
                  onChange={(e) => onAnswer(q.number, e.target.value)}
                >
                  <option value="">Select an answer</option>
                  {opts.map((o) => (
                    <option key={o.value} value={o.value}>
                      {g.type === "tfng" || g.type === "ynng"
                        ? o.label
                        : optionLabel(o)}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  id={"answer-" + q.number}
                  className="answer-input"
                  type="text"
                  aria-label={"Answer " + q.number}
                  placeholder="Type your answer"
                  autoComplete="off"
                  spellCheck={false}
                  maxLength={1000}
                  value={a.answers[q.number] || ""}
                  disabled={!editable}
                  onChange={(e) => onAnswer(q.number, e.target.value)}
                />
              )}
              {g.wordLimit && (
                <small className="word-limit">
                  {g.wordLimit === 1
                    ? "ONE WORD"
                    : `NO MORE THAN ${g.wordLimit} WORDS`}
                  {g.allowNumber ? " AND/OR A NUMBER" : ""}
                </small>
              )}
              {results[q.number] && <AnswerFeedback row={results[q.number]} />}
            </div>
          );
        })
      )}
    </div>
  );
}
function PassageBreakdown({
  result,
  listening = false,
}: {
  result: Result;
  listening?: boolean;
}) {
  const groups: Record<
    number,
    { correct: number; total: number; blank: number }
  > = {};
  result.rows.forEach((r) => {
    const g = (groups[r.passage] ??= { correct: 0, total: 0, blank: 0 });
    g.total++;
    g.correct += Number(r.status === "correct");
    g.blank += Number(r.status === "blank");
  });
  return (
    <div className="passage-breakdown">
      {Object.entries(groups).map(([n, g]) => (
        <div key={n}>
          <span>
            {listening ? "Part" : "Passage"} {n}
          </span>
          <strong>
            {g.correct}/{g.total}
          </strong>
          <small>{g.blank} câu bỏ trống</small>
        </div>
      ))}
    </div>
  );
}
function AnswerFeedback({
  row,
}: {
  row: NonNullable<Attempt["result"]>["rows"][number];
}) {
  return (
    <div className={"answer-feedback " + row.status}>
      {row.status === "correct" ? <Check size={14} /> : <X size={14} />}
      <span>
        {row.status === "correct"
          ? "Đúng"
          : row.status === "blank"
          ? "Bỏ trống"
          : "Sai"}{" "}
        · Đáp án: <strong>{row.accepted.join(" / ")}</strong>
        {row.groupNumbers && (
          <small>Nhóm {row.groupNumbers.join("–")}, không xét thứ tự</small>
        )}
      </span>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
