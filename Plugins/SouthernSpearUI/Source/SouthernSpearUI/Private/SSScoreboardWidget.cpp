// Copyright Southern Spear. All Rights Reserved.

#include "SSScoreboardWidget.h"

#include "Engine/World.h"
#include "SSScoreboardState.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

namespace
{
	constexpr float ColumnWidth = 520.f;
	const float StatWidths[] = { 44.f, 44.f, 44.f, 64.f };

	UTextBlock* Cell(UWidgetTree* T, UHorizontalBox* Line, float Width, bool bBold, const FLinearColor& Colour, int32 Size = 14)
	{
		UTextBlock* Text = SSWidgetKit::Text(T, Size, bBold, Colour);
		if (Width > 0.f)
		{
			USizeBox* Box = T->ConstructWidget<USizeBox>();
			Box->SetWidthOverride(Width);
			Text->SetJustification(ETextJustify::Right);
			Box->AddChild(Text);
			AddH(Line, Box);
		}
		else
		{
			AddH(Line, Text, true);
		}
		return Text;
	}
}

bool USSScoreboardWidget::Initialize()
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

	UVerticalBox* Frame = T->ConstructWidget<UVerticalBox>();
	Panel = Frame;
	Pin(Root, Frame, FVector2D(0.5f, 0.5f), FVector2D(0.f, 60.f)); // below the objective panel
	AddV(Frame, Rule(T, SSPalette::Brass500(), 2.f, 2 * ColumnWidth + 72.f));
	UBorder* Body = Plate(T, SSPalette::Ink900(0.93f), FMargin(24.f, 18.f, 24.f, 22.f));
	AddV(Frame, Body);
	UVerticalBox* Col = T->ConstructWidget<UVerticalBox>();
	Body->SetContent(Col);

	UHorizontalBox* Head = T->ConstructWidget<UHorizontalBox>();
	AddV(Col, Head);
	UVerticalBox* Titles = T->ConstructWidget<UVerticalBox>();
	AddH(Head, Titles, true);
	UTextBlock* Kicker = Text(T, 11, true, SSPalette::Brass300(), 300);
	Kicker->SetText(NSLOCTEXT("SSScore", "Kicker", "OBJECTIVE ASSAULT"));
	AddV(Titles, Kicker);
	UTextBlock* Title = Text(T, 30, true, SSPalette::Sand100(), 100);
	Title->SetText(NSLOCTEXT("SSScore", "Title", "SCOREBOARD"));
	AddV(Titles, Title);
	UTextBlock* Hint = Text(T, 11, true, SSPalette::Sage400(), 200);
	Hint->SetText(NSLOCTEXT("SSScore", "Hint", "HOLD TAB"));
	AddH(Head, Hint, false, VAlign_Bottom);

	UHorizontalBox* Columns = T->ConstructWidget<UHorizontalBox>();
	AddV(Col, Columns, 14.f);
	const FText SideNames[] = { NSLOCTEXT("SSScore", "Friendly", "3 ACR  ·  FRIENDLY"), NSLOCTEXT("SSScore", "Opposing", "MAF  ·  OPPOSING") };
	const FLinearColor Accents[] = { SSPalette::Sage200(), SSPalette::Opfor300() };
	for (int32 Side = 0; Side < 2; ++Side)
	{
		UVerticalBox* Table = T->ConstructWidget<UVerticalBox>();
		USizeBox* TableSize = T->ConstructWidget<USizeBox>();
		TableSize->SetWidthOverride(ColumnWidth);
		TableSize->AddChild(Table);
		AddH(Columns, TableSize, false, VAlign_Top)->SetPadding(FMargin(Side == 0 ? 0.f : 24.f, 0.f, 0.f, 0.f));

		// Side header: accent bar, name, kill total.
		AddV(Table, Rule(T, Accents[Side], 3.f));
		UHorizontalBox* SideHead = T->ConstructWidget<UHorizontalBox>();
		AddV(Table, SideHead, 8.f);
		UTextBlock* SideName = Text(T, 16, true, Accents[Side], 160);
		SideName->SetText(SideNames[Side]);
		AddH(SideHead, SideName, true);
		UTextBlock* Total = Text(T, 16, true, SSPalette::Sand100());
		AddH(SideHead, Total);
		Totals.Add(Total);

		// Column labels.
		UHorizontalBox* Labels = T->ConstructWidget<UHorizontalBox>();
		AddV(Table, Labels, 10.f);
		const TCHAR* LabelText[] = { TEXT("PLAYER"), TEXT("K"), TEXT("D"), TEXT("A"), TEXT("PING") };
		UBorder* LabelPad = Plate(T, FLinearColor::Transparent, FMargin(12.f, 0.f));
		UHorizontalBox* LabelLine = T->ConstructWidget<UHorizontalBox>();
		LabelPad->SetContent(LabelLine);
		AddH(Labels, LabelPad, true);
		for (int32 Index = 0; Index < 5; ++Index)
		{
			UTextBlock* Label = Cell(T, LabelLine, Index == 0 ? 0.f : StatWidths[Index - 1], true, SSPalette::Sage400(), 11);
			Label->SetText(FText::FromString(LabelText[Index]));
		}
		AddV(Table, Rule(T, SSPalette::Line(), 1.f), 6.f);

		for (int32 Index = 0; Index < RowsPerSide; ++Index)
		{
			FRowWidgets Row;
			Row.Plate = Plate(T, SSPalette::Field800(Index % 2 ? 0.55f : 0.8f), FMargin(12.f, 6.f));
			UHorizontalBox* Line = T->ConstructWidget<UHorizontalBox>();
			Row.Plate->SetContent(Line);
			Row.Name = Cell(T, Line, 0.f, false, SSPalette::Sand100(), 14);
			Row.Kills = Cell(T, Line, StatWidths[0], true, SSPalette::Sand100(), 15);
			Row.Deaths = Cell(T, Line, StatWidths[1], true, SSPalette::Sage200(), 15);
			Row.Assists = Cell(T, Line, StatWidths[2], true, SSPalette::Sage200(), 15);
			Row.Ping = Cell(T, Line, StatWidths[3], true, SSPalette::Sage400(), 13);
			AddV(Table, Row.Plate, 2.f);
			Keep.Add(Row.Plate);
			Sides[Side].Add(Row);
		}
	}
	return true;
}

void USSScoreboardWidget::Refresh()
{
	const USSScoreboardState* State = GetWorld() ? GetWorld()->GetSubsystem<USSScoreboardState>() : nullptr;
	if (!State)
	{
		return;
	}
	TArray<const FSSScoreRow*> Split[2];
	for (const FSSScoreRow& Row : State->Rows)
	{
		// Viewer-relative: the viewer's own team is always the left, friendly side.
		const bool bFriendly = State->LocalTeam != ESSTeamId::None ? Row.Team == State->LocalTeam : Row.Team == ESSTeamId::TeamOne;
		Split[bFriendly ? 0 : 1].Add(&Row);
	}
	for (int32 Side = 0; Side < 2; ++Side)
	{
		int32 Kills = 0;
		for (int32 Index = 0; Index < RowsPerSide; ++Index)
		{
			FRowWidgets& Widgets = Sides[Side][Index];
			const FSSScoreRow* Row = Split[Side].IsValidIndex(Index) ? Split[Side][Index] : nullptr;
			Widgets.Plate->SetVisibility(Row ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
			if (!Row)
			{
				continue;
			}
			Kills += Row->Kills;
			Widgets.Plate->SetBrushColor(Row->bLocal ? SSPalette::Brass500(0.28f) : SSPalette::Field800(Index % 2 ? 0.55f : 0.8f));
			Widgets.Name->SetText(FText::FromString(Row->bBot ? Row->Name + TEXT("  ·  BOT") : Row->Name));
			Widgets.Name->SetColorAndOpacity(Row->bLocal ? SSPalette::Brass300() : SSPalette::Sand100());
			Widgets.Kills->SetText(FText::AsNumber(Row->Kills));
			Widgets.Deaths->SetText(FText::AsNumber(Row->Deaths));
			Widgets.Assists->SetText(FText::AsNumber(Row->Assists));
			Widgets.Ping->SetText(Row->PingMs < 0 ? FText::FromString(TEXT("—")) : FText::FromString(FString::Printf(TEXT("%d ms"), Row->PingMs)));
		}
		Totals[Side]->SetText(FText::Format(NSLOCTEXT("SSScore", "Total", "{0} K"), FText::AsNumber(Kills)));
	}
}

void USSScoreboardWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;
	RefreshIn -= InDeltaTime;
	if (RefreshIn <= 0.f)
	{
		RefreshIn = 0.25f;
		Refresh();
	}
}
