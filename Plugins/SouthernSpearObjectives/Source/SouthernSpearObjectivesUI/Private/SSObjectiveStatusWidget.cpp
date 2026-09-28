// Copyright Southern Spear. All Rights Reserved.

#include "SSObjectiveStatusWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "GameFramework/PlayerController.h"
#include "GenericTeamAgentInterface.h"
#include "SSObjectiveActor.h"
#include "SSObjectiveHudModel.h"
#include "SSUIStyle.h"
#include "Styling/CoreStyle.h"
#include "SSFonts.h"

namespace
{
	constexpr float PanelWidth = 204.f; // matches the minimap above it (top right)
	constexpr int32 MaxChips = 6;

	UTextBlock* MakeText(UWidgetTree* Tree, int32 Size, bool bBold, const FLinearColor& Colour, int32 LetterSpacing = 0)
	{
		UTextBlock* Text = Tree->ConstructWidget<UTextBlock>();
		FSlateFontInfo Font = bBold ? SSFonts::Display(Size) : SSFonts::Body(Size);
		Font.LetterSpacing = LetterSpacing;
		Text->SetFont(Font);
		Text->SetColorAndOpacity(Colour);
		Text->SetShadowOffset(FVector2D(1.f, 1.f));
		Text->SetShadowColorAndOpacity(SSUIStyle::Ink950(0.6f));
		return Text;
	}

	UBorder* MakeBorder(UWidgetTree* Tree, const FLinearColor& Colour, const FMargin& Padding)
	{
		UBorder* Border = Tree->ConstructWidget<UBorder>();
		Border->SetBrushColor(Colour);
		Border->SetPadding(Padding);
		return Border;
	}

	UHorizontalBoxSlot* AddH(UHorizontalBox* Box, UWidget* Child, bool bFill = false, EVerticalAlignment V = VAlign_Center)
	{
		UHorizontalBoxSlot* Slot = Box->AddChildToHorizontalBox(Child);
		Slot->SetVerticalAlignment(V);
		Slot->SetSize(FSlateChildSize(bFill ? ESlateSizeRule::Fill : ESlateSizeRule::Automatic));
		return Slot;
	}

	UVerticalBoxSlot* AddV(UVerticalBox* Box, UWidget* Child, float Top = 0.f)
	{
		UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Child);
		Slot->SetHorizontalAlignment(HAlign_Fill);
		Slot->SetPadding(FMargin(0.f, Top, 0.f, 0.f));
		return Slot;
	}

	UWidget* Rule(UWidgetTree* Tree, const FLinearColor& Colour, float Height)
	{
		USizeBox* Size = Tree->ConstructWidget<USizeBox>();
		Size->SetHeightOverride(Height);
		Size->AddChild(MakeBorder(Tree, Colour, FMargin(0.f)));
		return Size;
	}

	FText Upper(const FText& Text) { return Text.ToUpper(); }
}

bool USSObjectiveStatusWidget::Initialize()
{
	if (!Super::Initialize())
	{
		return false;
	}
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return true;
	}
	UWidgetTree* T = WidgetTree;

	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;

	// Panel: top right, directly under the minimap, the same width. Field-dark plate with a brass top edge.
	UVerticalBox* Frame = T->ConstructWidget<UVerticalBox>();
	UCanvasPanelSlot* FrameSlot = Root->AddChildToCanvas(Frame);
	FrameSlot->SetAnchors(FAnchors(1.f, 0.f));
	FrameSlot->SetAlignment(FVector2D(1.f, 0.f));
	FrameSlot->SetPosition(FVector2D(-20.f, 212.f));
	FrameSlot->SetAutoSize(true);

	AddV(Frame, Rule(T, SSUIStyle::Brass500(), 2.f));
	UBorder* Plate = MakeBorder(T, SSUIStyle::Ink900(0.72f), FMargin(10.f, 6.f, 10.f, 8.f));
	AddV(Frame, Plate);

	USizeBox* Width = T->ConstructWidget<USizeBox>();
	Width->SetWidthOverride(PanelWidth - 20.f);
	Plate->SetContent(Width);
	UVerticalBox* Body = T->ConstructWidget<UVerticalBox>();
	Width->AddChild(Body);

	// Row 1: ROUND 3 ........ ASSAULT 12:34
	UHorizontalBox* Top = T->ConstructWidget<UHorizontalBox>();
	AddV(Body, Top);
	RoundText = MakeText(T, 10, true, SSUIStyle::Brass300(), 120);
	AddH(Top, RoundText, false, VAlign_Bottom);
	AddH(Top, T->ConstructWidget<USpacer>(), true);
	PhaseText = MakeText(T, 9, true, SSUIStyle::Sage400(), 120);
	AddH(Top, PhaseText, false, VAlign_Bottom)->SetPadding(FMargin(0.f, 0.f, 6.f, 2.f));
	ClockText = MakeText(T, 16, true, SSUIStyle::Sand100(), 20);
	AddH(Top, ClockText, false, VAlign_Bottom);

	AddV(Body, Rule(T, SSUIStyle::Line(0.9f), 1.f), 4.f);

	// Row 2: [A][B]  OBJ B  FARMSTEAD ........ OPPOSING CAPTURING
	ObjectiveRow = T->ConstructWidget<UHorizontalBox>();
	AddV(Body, ObjectiveRow, 5.f);
	for (int32 Index = 0; Index < MaxChips; ++Index)
	{
		FChipWidgets Chip;
		Chip.Outline = MakeBorder(T, SSUIStyle::Line(), FMargin(1.5f));
		USizeBox* ChipSize = T->ConstructWidget<USizeBox>();
		ChipSize->SetWidthOverride(18.f);
		ChipSize->SetHeightOverride(18.f);
		Chip.Outline->SetContent(ChipSize);
		Chip.Fill = MakeBorder(T, SSUIStyle::Field800(), FMargin(0.f));
		Chip.Fill->SetHorizontalAlignment(HAlign_Center);
		Chip.Fill->SetVerticalAlignment(VAlign_Center);
		ChipSize->AddChild(Chip.Fill);
		Chip.Letter = MakeText(T, 9, true, SSUIStyle::Sand100());
		Chip.Fill->SetContent(Chip.Letter);
		AddH(ObjectiveRow, Chip.Outline)->SetPadding(FMargin(0.f, 0.f, 3.f, 0.f));
		Chips.Add(Chip);
	}
	ObjectiveNameText = MakeText(T, 11, true, SSUIStyle::Sand100(), 40);
	AddH(ObjectiveRow, ObjectiveNameText, false, VAlign_Center)->SetPadding(FMargin(5.f, 0.f, 0.f, 0.f));
	// Status on its own line: the panel is narrow.
	StatusRow = T->ConstructWidget<UHorizontalBox>();
	AddV(Body, StatusRow, 4.f);
	StatusText = MakeText(T, 9, true, SSUIStyle::Sage400(), 120);
	AddH(StatusRow, StatusText, true);
	AliveText = MakeText(T, 9, true, SSUIStyle::Sand100(), 120);
	AddH(StatusRow, AliveText, false, VAlign_Bottom);

	// Capture bar: two fill-weighted segments, so no engine bar style is needed.
	USizeBox* BarSize = T->ConstructWidget<USizeBox>();
	BarSize->SetHeightOverride(4.f);
	AddV(Body, BarSize, 3.f);
	UHorizontalBox* Bar = T->ConstructWidget<UHorizontalBox>();
	BarSize->AddChild(Bar);
	BarFill = MakeBorder(T, SSUIStyle::Sage400(), FMargin(0.f));
	BarRest = MakeBorder(T, SSUIStyle::Field700(), FMargin(0.f));
	BarFillSlot = AddH(Bar, BarFill, true, VAlign_Fill);
	BarRestSlot = AddH(Bar, BarRest, true, VAlign_Fill);
	BarSizeBox = BarSize;

	// Row 4: FRIENDLY 1  —  0 OPPOSING
	UHorizontalBox* Score = T->ConstructWidget<UHorizontalBox>();
	AddV(Body, Score, 6.f);
	FirstSideText = MakeText(T, 9, true, SSUIStyle::Sage200(), 100);
	FirstScoreText = MakeText(T, 13, true, SSUIStyle::Sand100());
	UTextBlock* Dash = MakeText(T, 11, false, SSUIStyle::Line());
	Dash->SetText(FText::FromString(TEXT("—")));
	SecondScoreText = MakeText(T, 13, true, SSUIStyle::Sand100());
	SecondSideText = MakeText(T, 9, true, SSUIStyle::Opfor300(), 100);
	AddH(Score, T->ConstructWidget<USpacer>(), true);
	AddH(Score, FirstSideText, false, VAlign_Center)->SetPadding(FMargin(0.f, 0.f, 5.f, 0.f));
	AddH(Score, FirstScoreText);
	AddH(Score, Dash)->SetPadding(FMargin(6.f, 0.f));
	AddH(Score, SecondScoreText);
	AddH(Score, SecondSideText, false, VAlign_Center)->SetPadding(FMargin(5.f, 0.f, 0.f, 0.f));
	AddH(Score, T->ConstructWidget<USpacer>(), true);

	SetVisibility(ESlateVisibility::HitTestInvisible);
	return true;
}

void USSObjectiveStatusWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);

	const ASSObjectiveAssaultDirector* Dir = Director.Get();
	if (!Dir || !RoundText)
	{
		return;
	}

	ESSTeamId ViewerTeam = ESSTeamId::None;
	if (const IGenericTeamAgentInterface* Agent = Cast<IGenericTeamAgentInterface>(GetOwningPlayer()))
	{
		ViewerTeam = Dir->ToTeamId(Agent->GetGenericTeamId());
	}

	const FSSRoundState& Round = Dir->GetRoundState();
	const TArray<TObjectPtr<ASSObjectiveActor>>& Objectives = Dir->GetObjectives();
	const ASSObjectiveActor* Active = Objectives.IsValidIndex(Round.ActiveObjectiveIndex) ? Objectives[Round.ActiveObjectiveIndex].Get() : nullptr;

	FSSObjectiveHudModel Model = FSSObjectiveHudModel::Build(
		Round, Active ? &Active->GetObjectiveState() : nullptr,
		Active ? Active->ObjectiveName : FText::GetEmpty(), ViewerTeam);
	if (Dir->IsSectionAssault())
	{
		Model.ApplySectionAssault(Round, Dir->GetMatchState(), ViewerTeam);
	}

	TArray<FSSObjectiveState> States;
	for (const ASSObjectiveActor* Objective : Objectives)
	{
		States.Add(Objective ? Objective->GetObjectiveState() : FSSObjectiveState());
	}
	Model.BuildChips(States, Round.ActiveObjectiveIndex, ViewerTeam);

	RoundText->SetText(Upper(Model.RoundLabel));
	PhaseText->SetText(Upper(Model.PhaseLabel));
	ClockText->SetText(Model.Clock);
	ClockText->SetColorAndOpacity(Round.Phase == ESSRoundPhase::InProgress && Round.PhaseTimeRemaining <= 30.f
		? SSUIStyle::Opfor300() : SSUIStyle::Sand100());

	for (int32 Index = 0; Index < Chips.Num(); ++Index)
	{
		FChipWidgets& W = Chips[Index];
		if (!Model.Chips.IsValidIndex(Index))
		{
			W.Outline->SetVisibility(ESlateVisibility::Collapsed);
			continue;
		}
		const FSSObjectiveHudModel::FChip& C = Model.Chips[Index];
		const bool bOwned = C.OwnerTone != ESSObjectiveHudTone::Neutral;
		W.Outline->SetVisibility(ESlateVisibility::HitTestInvisible);
		W.Outline->SetBrushColor(C.bActive ? SSUIStyle::Brass500() : SSUIStyle::Line());
		W.Fill->SetBrushColor(bOwned ? SSUIStyle::ToneColour(C.OwnerTone) * FLinearColor(0.55f, 0.55f, 0.55f, 1.f) : SSUIStyle::Field800());
		W.Letter->SetText(C.Letter);
		W.Letter->SetColorAndOpacity(C.bActive || bOwned ? SSUIStyle::Sand100() : SSUIStyle::Sage400());
	}

	const bool bShowObjective = Model.bShowObjective;
	ObjectiveNameText->SetText(bShowObjective ? Upper(Model.ObjectiveName) : Upper(Model.Header));
	StatusText->SetText(Upper(Model.ObjectiveStatus));
	StatusText->SetColorAndOpacity(SSUIStyle::ToneColour(Model.ProgressTone));
	StatusRow->SetVisibility(bShowObjective ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	AliveText->SetText(Upper(Model.Alive));
	AliveText->SetVisibility(Model.Alive.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	BarSizeBox->SetVisibility(bShowObjective ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);

	const float P = FMath::Clamp(Model.Progress, 0.f, 1.f);
	FSlateChildSize FillSize(ESlateSizeRule::Fill); FillSize.Value = FMath::Max(P, 0.0001f);
	FSlateChildSize RestSize(ESlateSizeRule::Fill); RestSize.Value = FMath::Max(1.f - P, 0.0001f);
	BarFillSlot->SetSize(FillSize);
	BarRestSlot->SetSize(RestSize);
	BarFill->SetBrushColor(SSUIStyle::ToneColour(Model.ProgressTone));

	FirstSideText->SetText(Upper(Model.FirstSide));
	SecondSideText->SetText(Upper(Model.SecondSide));
	FirstSideText->SetColorAndOpacity(SSUIStyle::ToneColour(Model.FirstTone));
	SecondSideText->SetColorAndOpacity(SSUIStyle::ToneColour(Model.SecondTone));
	FirstScoreText->SetText(FText::AsNumber(Model.FirstScore));
	SecondScoreText->SetText(FText::AsNumber(Model.SecondScore));
}
